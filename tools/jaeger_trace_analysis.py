#!/usr/bin/env python3
"""Export sanitized Jaeger traces and derive runtime dependency measurements."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import statistics
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    low, high = math.floor(position), math.ceil(position)
    return ordered[low] if low == high else ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def tag_map(span: dict) -> dict:
    # Allow-list only architectural attributes; never export request headers,
    # bodies, cookies, tokens, query strings, or arbitrary span attributes.
    allowed = {
        "span.kind", "http.request.method", "http.method", "http.route",
        "http.target", "url.path", "http.response.status_code",
        "http.status_code", "error.type", "otel.status_code", "db.system",
        "db.operation.name", "db.operation", "db.namespace", "server.address", "server.port",
    }
    return {tag.get("key"): tag.get("value") for tag in span.get("tags", []) if tag.get("key") in allowed}


def load_scenarios(path: Path) -> dict[str, tuple[str, str]]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as handle:
        return {row["trace_id"]: (row["scenario"], row["iteration"]) for row in csv.DictReader(handle) if row.get("trace_id")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jaeger-url", default="http://localhost:16686")
    parser.add_argument("--scenario-requests", type=Path,
                        default=ROOT / "docs/discovery/dynamic-generated-otel/scenario-requests.csv")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "docs/discovery/dynamic-generated-otel")
    parser.add_argument("--lookback", default="1h")
    parser.add_argument("--limit", type=int, default=1000)
    args = parser.parse_args()
    out = args.output.resolve()
    scenario_map = load_scenarios(args.scenario_requests.resolve())

    services = get_json(args.jaeger_url.rstrip("/") + "/api/services").get("data", [])
    traces: dict[str, dict] = {}
    for service in services:
        query = urllib.parse.urlencode({"service": service, "lookback": args.lookback, "limit": args.limit})
        payload = get_json(args.jaeger_url.rstrip("/") + "/api/traces?" + query)
        for trace in payload.get("data", []):
            traces[trace["traceID"]] = trace

    span_rows, edge_samples, database_samples, chain_rows = [], [], [], []
    for trace_id, trace in sorted(traces.items()):
        processes = trace.get("processes", {})
        spans = trace.get("spans", [])
        by_id = {span["spanID"]: span for span in spans}
        scenario, iteration = scenario_map.get(trace_id, ("UNMATCHED", ""))
        trace_rows = []
        for span in spans:
            tags = tag_map(span)
            service = processes.get(span.get("processID"), {}).get("serviceName", "UNKNOWN")
            parents = [r.get("spanID") for r in span.get("references", []) if r.get("refType") == "CHILD_OF"]
            parent_id = parents[0] if parents else ""
            status = tags.get("http.response.status_code", tags.get("http.status_code", ""))
            error = bool(tags.get("error.type")) or str(tags.get("otel.status_code", "")).upper() == "ERROR"
            route = tags.get("http.route", tags.get("url.path", tags.get("http.target", "")))
            if "?" in str(route):
                route = str(route).split("?", 1)[0]
            row = {
                "trace_id": trace_id, "scenario": scenario, "iteration": iteration,
                "span_id": span["spanID"], "parent_span_id": parent_id,
                "service": service, "operation": span.get("operationName", ""),
                "span_kind": tags.get("span.kind", ""),
                "start_time_utc": dt.datetime.fromtimestamp(span["startTime"] / 1_000_000, dt.timezone.utc).isoformat(),
                "duration_ms": round(span.get("duration", 0) / 1000, 3),
                "http_method": tags.get("http.request.method", tags.get("http.method", "")),
                "http_route": route, "http_status": status, "error": str(error).lower(),
            }
            span_rows.append(row)
            trace_rows.append(row)
            if tags.get("db.system"):
                database_samples.append({"trace_id": trace_id, "scenario": scenario, "service": service,
                                         "db_system": tags.get("db.system", ""),
                                         "db_operation": tags.get("db.operation.name", tags.get("db.operation", "")),
                                         "db_namespace": tags.get("db.namespace", ""),
                                         "server_address": tags.get("server.address", ""),
                                         "server_port": tags.get("server.port", ""),
                                         "duration_ms": row["duration_ms"], "error": error})
            parent = by_id.get(parent_id)
            if parent:
                parent_service = processes.get(parent.get("processID"), {}).get("serviceName", "UNKNOWN")
                if parent_service != service:
                    edge_samples.append({"trace_id": trace_id, "scenario": scenario,
                                         "caller": parent_service, "callee": service,
                                         "http_method": row["http_method"], "http_route": row["http_route"],
                                         "duration_ms": row["duration_ms"], "http_status": status, "error": error})
        if trace_rows and scenario != "UNMATCHED":
            ordered_services = []
            for row in sorted(trace_rows, key=lambda r: r["start_time_utc"]):
                if row["service"] not in ordered_services:
                    ordered_services.append(row["service"])
            starts = [dt.datetime.fromisoformat(r["start_time_utc"]) for r in trace_rows]
            ends = [start + dt.timedelta(milliseconds=r["duration_ms"]) for start, r in zip(starts, trace_rows)]
            chain_rows.append({"trace_id": trace_id, "scenario": scenario, "iteration": iteration,
                               "services": " -> ".join(ordered_services), "service_count": len(ordered_services),
                               "span_count": len(trace_rows),
                               "trace_duration_ms": round((max(ends) - min(starts)).total_seconds() * 1000, 3),
                               "error_spans": sum(r["error"] == "true" for r in trace_rows)})

    fields = ["trace_id", "scenario", "iteration", "span_id", "parent_span_id", "service", "operation",
              "span_kind", "start_time_utc", "duration_ms", "http_method", "http_route", "http_status", "error"]
    write_csv(out / "trace-spans.csv", span_rows, fields)

    grouped = defaultdict(list)
    for row in edge_samples:
        grouped[(row["scenario"], row["caller"], row["callee"], row["http_method"], row["http_route"])].append(row)
    edges = []
    for key, values in sorted(grouped.items()):
        durations = [v["duration_ms"] for v in values]
        edges.append({"scenario": key[0], "caller": key[1], "callee": key[2], "http_method": key[3],
                      "http_route": key[4], "request_count": len(values),
                      "failure_count": sum(bool(v["error"]) or str(v["http_status"]).startswith("5") for v in values),
                      "latency_mean_ms": round(statistics.mean(durations), 3),
                      "latency_p95_ms": round(percentile(durations, .95), 3),
                      "latency_max_ms": round(max(durations), 3)})
    edge_fields = ["scenario", "caller", "callee", "http_method", "http_route", "request_count",
                   "failure_count", "latency_mean_ms", "latency_p95_ms", "latency_max_ms"]
    write_csv(out / "trace-edges.csv", edges, edge_fields)
    write_csv(out / "trace-chains.csv", chain_rows,
              ["trace_id", "scenario", "iteration", "services", "service_count", "span_count", "trace_duration_ms", "error_spans"])

    db_grouped = defaultdict(list)
    for row in database_samples:
        db_grouped[(row["scenario"], row["service"], row["db_system"], row["db_operation"],
                    row["db_namespace"], row["server_address"], row["server_port"])].append(row)
    databases = []
    for key, values in sorted(db_grouped.items()):
        durations = [v["duration_ms"] for v in values]
        databases.append({"scenario": key[0], "service": key[1], "db_system": key[2], "db_operation": key[3],
                          "db_namespace": key[4], "server_address": key[5], "server_port": key[6],
                          "span_count": len(values), "failure_count": sum(bool(v["error"]) for v in values),
                          "latency_mean_ms": round(statistics.mean(durations), 3),
                          "latency_p95_ms": round(percentile(durations, .95), 3),
                          "latency_max_ms": round(max(durations), 3)})
    write_csv(out / "trace-databases.csv", databases,
              ["scenario", "service", "db_system", "db_operation", "db_namespace", "server_address", "server_port",
               "span_count", "failure_count", "latency_mean_ms", "latency_p95_ms", "latency_max_ms"])

    static_path = ROOT / "docs/discovery/generated/http-dependencies.csv"
    with static_path.open(encoding="utf-8-sig", newline="") as handle:
        static_pairs = {(r["caller"], r["callee"]) for r in csv.DictReader(handle)}
    runtime_pairs = {(r["caller"], r["callee"]) for r in edges}
    comparison = []
    for caller, callee in sorted(static_pairs | runtime_pairs):
        in_static, in_runtime = (caller, callee) in static_pairs, (caller, callee) in runtime_pairs
        classification = "OBSERVED_IN_BOTH" if in_static and in_runtime else "RUNTIME_ONLY" if in_runtime else "NOT_EXERCISED"
        comparison.append({"caller": caller, "callee": callee, "classification": classification,
                           "static_evidence": str(in_static).lower(), "trace_evidence": str(in_runtime).lower(),
                           "interpretation": "absence is workload-specific, not proof of an unused dependency" if not in_runtime else "observed in distributed trace"})
    write_csv(out / "static-trace-comparison.csv", comparison,
              ["caller", "callee", "classification", "static_evidence", "trace_evidence", "interpretation"])
    summary = {
        "exported_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "jaeger_services": sorted(services), "unique_traces": len(traces),
        "scenario_matched_traces": sum(trace_id in scenario_map for trace_id in traces),
        "spans": len(span_rows), "cross_service_edge_groups": len(edges),
        "scenario_trace_chains": len(chain_rows), "database_span_groups": len(databases),
        "dependency_classifications": dict(Counter(r["classification"] for r in comparison)),
        "unmatched_traces": sum(trace_id not in scenario_map for trace_id in traces),
        "classification_note": "UNMATCHED traces are background or outside the controlled workload.",
    }
    (out / "trace-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
