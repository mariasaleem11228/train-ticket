#!/usr/bin/env python3
"""Read-only dynamic baseline collector for the TrainTicket Docker deployment.

Uses only the Python standard library. It never writes to containers and never
stores credentials, cookies, authorization headers, or response bodies.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import http.cookiejar
import json
import math
import re
import secrets
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "docs" / "discovery" / "dynamic-generated"
PROJECT = "train-ticket"
FAILURE_PATTERNS = {
    "exception": re.compile(r"\bexception\b", re.I),
    "timeout": re.compile(r"\btime(?:d|s)?[ -]?out\b", re.I),
    "connection_refused": re.compile(r"connection refused", re.I),
    "unavailable": re.compile(r"\b(service )?unavailable\b", re.I),
    "http_5xx": re.compile(r"\b(?:status[=: ]+|HTTP/\d(?:\.\d)?[\" ]+)(5\d\d)\b", re.I),
}


def docker(*args: str, check: bool = True) -> str:
    p = subprocess.run(["docker", *args], cwd=ROOT, text=True,
                       encoding="utf-8", errors="replace", capture_output=True)
    if check and p.returncode:
        raise RuntimeError(f"docker {' '.join(args)} failed: {p.stderr.strip()}")
    return p.stdout


def json_lines(text: str) -> list[dict]:
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or (list(rows[0]) if rows else [])
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return ordered[lo] if lo == hi else ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)


def human_bytes(value: str) -> int | None:
    match = re.fullmatch(r"\s*([\d.]+)\s*([kKmMgGtT]?i?[bB])\s*", value)
    if not match:
        return None
    units = {"b": 1, "kb": 1000, "kib": 1024, "mb": 1000**2,
             "mib": 1024**2, "gb": 1000**3, "gib": 1024**3,
             "tb": 1000**4, "tib": 1024**4}
    return round(float(match.group(1)) * units[match.group(2).lower()])


def inventory() -> tuple[list[dict], dict[str, str], dict[str, str]]:
    ids = docker("ps", "-q", "--filter", f"label=com.docker.compose.project={PROJECT}").split()
    if not ids:
        raise RuntimeError(f"no running containers found for Compose project {PROJECT!r}")
    inspected = json.loads(docker("inspect", *ids))
    rows, ip_to_service, container_to_service = [], {}, {}
    for c in inspected:
        labels = c["Config"].get("Labels") or {}
        service = labels.get("com.docker.compose.service", c["Name"].lstrip("/"))
        container_to_service[c["Id"][:12]] = service
        networks = c["NetworkSettings"].get("Networks") or {}
        ips = sorted(n.get("IPAddress", "") for n in networks.values() if n.get("IPAddress"))
        for ip in ips:
            ip_to_service[ip] = service
        state = c["State"]
        image_ref = c["Config"].get("Image", "")
        image = json.loads(docker("image", "inspect", c["Image"]))[0]
        rows.append({
            "service": service, "container_id": c["Id"][:12], "container_name": c["Name"].lstrip("/"),
            "kind": "infrastructure" if ("mongo" in service or service in {"redis", "ts-voucher-mysql"}) else "application",
            "status": state.get("Status", ""), "started_at": state.get("StartedAt", ""),
            "restart_count": c.get("RestartCount", 0), "health": (state.get("Health") or {}).get("Status", "not_configured"),
            "image_reference": image_ref, "image_id": image.get("Id", ""),
            "image_repo_digests": ";".join(image.get("RepoDigests") or []),
            "image_created": image.get("Created", ""), "image_labels": json.dumps((image.get("Config") or {}).get("Labels") or {}, sort_keys=True),
            "ip_addresses": ";".join(ips),
        })
    return sorted(rows, key=lambda x: x["service"]), ip_to_service, container_to_service


def sample_stats(samples: int, interval: float) -> tuple[list[dict], list[dict]]:
    raw = []
    for index in range(samples):
        stamp = dt.datetime.now(dt.timezone.utc).isoformat()
        for item in json_lines(docker("stats", "--no-stream", "--format", "{{json .}}")):
            service = item.get("Name", "")
            prefix, suffix = f"{PROJECT}-", "-1"
            if service.startswith(prefix) and service.endswith(suffix):
                service = service[len(prefix):-len(suffix)]
            raw.append({"timestamp_utc": stamp, "sample": index + 1, "service": service,
                        "cpu_percent": float(item.get("CPUPerc", "0%").rstrip("%") or 0),
                        "memory_bytes": human_bytes(item.get("MemUsage", "").split("/")[0].strip()),
                        "memory_percent": float(item.get("MemPerc", "0%").rstrip("%") or 0),
                        "network_io": item.get("NetIO", ""), "block_io": item.get("BlockIO", ""),
                        "pids": item.get("PIDs", "")})
        if index + 1 < samples:
            time.sleep(interval)
    grouped = defaultdict(list)
    for row in raw:
        grouped[row["service"]].append(row)
    summary = []
    for service, values in sorted(grouped.items()):
        cpu = [v["cpu_percent"] for v in values]
        mem = [v["memory_bytes"] for v in values if v["memory_bytes"] is not None]
        summary.append({"service": service, "samples": len(values), "cpu_mean_percent": round(statistics.mean(cpu), 4),
                        "cpu_max_percent": round(max(cpu), 4), "memory_mean_bytes": round(statistics.mean(mem)) if mem else "",
                        "memory_max_bytes": max(mem) if mem else ""})
    return raw, summary


def tcp_snapshot(inventory_rows: list[dict], ip_map: dict[str, str]) -> list[dict]:
    rows = []
    for item in inventory_rows:
        if item["kind"] != "application":
            continue
        text = docker("exec", item["container_id"], "sh", "-c", "cat /proc/net/tcp /proc/net/tcp6 2>/dev/null", check=False)
        for line in text.splitlines():
            parts = line.split()
            if len(parts) < 4 or parts[0] == "sl":
                continue
            try:
                remote_hex, state = parts[2], parts[3]
                address, port_hex = remote_hex.split(":")
                if len(address) == 8:
                    remote_ip = ".".join(str(int(address[i:i+2], 16)) for i in range(6, -1, -2))
                else:
                    continue
                remote_port = int(port_hex, 16)
            except (ValueError, IndexError):
                continue
            callee = ip_map.get(remote_ip)
            # ESTABLISHED proves a live peer; TIME_WAIT preserves evidence of a
            # recently completed short-lived connection long enough to sample.
            state_name = {"01": "ESTABLISHED", "06": "TIME_WAIT"}.get(state)
            if callee and callee != item["service"] and state_name:
                rows.append({"caller": item["service"], "callee": callee, "remote_ip": remote_ip,
                             "remote_port": remote_port, "tcp_state": state_name,
                             "observation": "live_tcp_socket", "limitation": "connection, not HTTP request count"})
    unique = {(r["caller"], r["callee"], r["remote_port"]): r for r in rows}
    return sorted(unique.values(), key=lambda x: (x["caller"], x["callee"], x["remote_port"]))


def request(opener, method: str, url: str, body: dict | None, timeout: float, trace_id: str = "") -> dict:
    payload = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if trace_id:
        headers["traceparent"] = f"00-{trace_id}-{secrets.token_hex(8)}-01"
    req = urllib.request.Request(url, data=payload, headers=headers, method=method)
    start = time.perf_counter()
    try:
        with opener.open(req, timeout=timeout) as response:
            content, status = response.read(), response.status
        error = ""
    except urllib.error.HTTPError as exc:
        content, status, error = exc.read(), exc.code, f"HTTPError:{exc.code}"
    except Exception as exc:  # error type only: messages can contain sensitive URLs
        content, status, error = b"", 0, type(exc).__name__
    elapsed = (time.perf_counter() - start) * 1000
    app_status, app_message, response_shape, result_count = "", "", "unknown", ""
    try:
        parsed = json.loads(content)
        response_shape = type(parsed).__name__
        if isinstance(parsed, dict):
            app_status = parsed.get("status", "")
            app_message = parsed.get("msg", parsed.get("message", ""))
            if isinstance(parsed.get("data"), list):
                result_count = len(parsed["data"])
        elif isinstance(parsed, list):
            result_count = len(parsed)
    except (json.JSONDecodeError, UnicodeDecodeError):
        pass
    return {"http_status": status, "latency_ms": round(elapsed, 3), "response_bytes": len(content),
            "response_sha256": hashlib.sha256(content).hexdigest() if content else "",
            "application_status": app_status, "application_message": str(app_message)[:160],
            "response_shape": response_shape, "result_count": result_count, "error_type": error}


def run_scenarios(base_url: str, iterations: int, timeout: float, future_days: int) -> tuple[list[dict], list[dict]]:
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    departure_date = dt.datetime.now().astimezone().date() + dt.timedelta(days=future_days)
    # The deployed 0.2.0 images deserialize this field as java.util.Date even
    # though the checked-in UI sends a formatted string. Epoch milliseconds are
    # accepted by Jackson across legacy date-format configurations.
    departure = round(dt.datetime.combine(departure_date, dt.time(), tzinfo=dt.timezone.utc).timestamp() * 1000)
    definitions = [
        ("login", "POST", "/api/v1/users/login", {"username": "fdse_microservice", "password": "111111", "verificationCode": "1234"}),
        # The deployed 0.2.0 images package travel.entity.TripInfo with the
        # field `startingPlace`; this differs from the checked-in UI/common DTO
        # field `startPlace`. The workload targets the verified runtime API.
        ("search_g_train", "POST", "/api/v1/travelservice/trips/left", {"startingPlace": "Shang Hai", "endPlace": "Su Zhou", "departureTime": departure}),
        ("search_d_train", "POST", "/api/v1/travel2service/trips/left", {"startingPlace": "Shang Hai", "endPlace": "Su Zhou", "departureTime": departure}),
    ]
    rows = []
    for scenario, method, route, body in definitions:
        for iteration in range(1, iterations + 1):
            trace_id = secrets.token_hex(16)
            result = request(opener, method, base_url.rstrip("/") + route, body, timeout, trace_id)
            rows.append({"timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "scenario": scenario,
                         "iteration": iteration, "trace_id": trace_id, "method": method, "route": route, **result})
    summaries = []
    for scenario, method, route, _ in definitions:
        selected = [r for r in rows if r["scenario"] == scenario]
        latencies = [r["latency_ms"] for r in selected]
        failures = [r for r in selected if not (200 <= r["http_status"] < 400) or r["error_type"]]
        semantic_successes = sum(
            (str(r["application_status"]) == "1") if scenario == "login" else
            (isinstance(r["result_count"], int) and r["result_count"] > 0)
            for r in selected
        )
        summaries.append({"scenario": scenario, "method": method, "route": route, "requests": len(selected),
                          "successes": len(selected) - len(failures), "failures": len(failures),
                          "semantic_successes": semantic_successes, "empty_or_unsuccessful_results": len(selected) - semantic_successes,
                          "latency_min_ms": round(min(latencies), 3), "latency_mean_ms": round(statistics.mean(latencies), 3),
                          "latency_median_ms": round(statistics.median(latencies), 3),
                          "latency_p95_ms": round(percentile(latencies, .95), 3), "latency_max_ms": round(max(latencies), 3)})
    return rows, summaries


def compare_static_runtime(runtime_rows: list[dict]) -> list[dict]:
    static_path = ROOT / "docs" / "discovery" / "generated" / "http-dependencies.csv"
    catalog_path = ROOT / "docs" / "discovery" / "generated" / "service-catalog.csv"
    with static_path.open(encoding="utf-8-sig", newline="") as f:
        static_rows = list(csv.DictReader(f))
    with catalog_path.open(encoding="utf-8-sig", newline="") as f:
        catalog = {r["component"]: r for r in csv.DictReader(f)}
    static_pairs = {(r["caller"], r["callee"]) for r in static_rows}
    runtime_pairs = {(r["caller"], r["callee"]) for r in runtime_rows}
    rows = []
    for caller, callee in sorted(static_pairs | runtime_pairs):
        in_static, in_runtime = (caller, callee) in static_pairs, (caller, callee) in runtime_pairs
        image_only = any("image-only" in catalog.get(s, {}).get("classification", "") for s in (caller, callee))
        if in_static and in_runtime:
            classification = "OBSERVED_IN_BOTH"
        elif in_runtime and image_only:
            classification = "IMAGE_ONLY"
        elif in_runtime:
            classification = "RUNTIME_ONLY"
        else:
            classification = "NOT_EXERCISED"
        rows.append({"caller": caller, "callee": callee, "classification": classification,
                     "static_evidence": str(in_static).lower(), "runtime_evidence": str(in_runtime).lower(),
                     "interpretation": "absence is workload-specific, not proof of an unused dependency" if not in_runtime else "observed live TCP connection"})
    return rows


def log_findings(inventory_rows: list[dict], since: str) -> tuple[list[dict], list[dict]]:
    failures, startups = [], []
    started_re = re.compile(r"Started\s+(.+?)\s+in\s+([\d.]+)\s+seconds", re.I)
    for item in inventory_rows:
        if item["kind"] != "application":
            continue
        logs = docker("logs", "--since", since, item["container_id"], check=False)
        counts = Counter()
        examples = {}
        for line in logs.splitlines():
            for category, pattern in FAILURE_PATTERNS.items():
                if pattern.search(line):
                    counts[category] += 1
                    examples.setdefault(category, "matched; raw line withheld to avoid secret leakage")
            match = started_re.search(line)
            if match:
                startups.append({"service": item["service"], "application": match.group(1)[:120],
                                 "reported_startup_seconds": match.group(2), "evidence": "Spring Boot log"})
        for category, count in counts.items():
            failures.append({"service": item["service"], "category": category, "matching_log_lines": count,
                             "since": since, "note": examples[category]})
    return sorted(failures, key=lambda x: (x["service"], x["category"])), startups


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--stats-samples", type=int, default=5)
    parser.add_argument("--stats-interval", type=float, default=1.0)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--future-days", type=int, default=7)
    parser.add_argument("--base-url", default="http://localhost:8080")
    args = parser.parse_args()
    if args.iterations < 1 or args.stats_samples < 1:
        parser.error("iterations and stats-samples must be positive")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    started = dt.datetime.now(dt.timezone.utc)
    since = started.isoformat().replace("+00:00", "Z")
    inv, ip_map, _ = inventory()
    write_csv(output / "runtime-containers.csv", inv)
    raw_stats, stats_summary = sample_stats(args.stats_samples, args.stats_interval)
    write_csv(output / "resource-samples.csv", raw_stats)
    write_csv(output / "resource-summary.csv", stats_summary)
    before = tcp_snapshot(inv, ip_map)
    scenario_rows, scenario_summary = run_scenarios(args.base_url, args.iterations, args.timeout, args.future_days)
    after = tcp_snapshot(inv, ip_map)
    sockets = list({(r["caller"], r["callee"], r["remote_port"]): r for r in before + after}.values())
    write_csv(output / "runtime-connections.csv", sorted(sockets, key=lambda x: (x["caller"], x["callee"], x["remote_port"])),
              ["caller", "callee", "remote_ip", "remote_port", "tcp_state", "observation", "limitation"])
    write_csv(output / "scenario-requests.csv", scenario_rows)
    write_csv(output / "scenario-summary.csv", scenario_summary)
    comparison = compare_static_runtime(sockets)
    write_csv(output / "static-runtime-comparison.csv", comparison)
    failures, startups = log_findings(inv, since)
    write_csv(output / "failure-summary.csv", failures,
              ["service", "category", "matching_log_lines", "since", "note"])
    write_csv(output / "startup-summary.csv", startups,
              ["service", "application", "reported_startup_seconds", "evidence"])
    summary = {
        "schema_version": 1, "collection_started_utc": started.isoformat(),
        "collection_finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "compose_project": PROJECT, "running_containers": len(inv),
        "application_containers": sum(r["kind"] == "application" for r in inv),
        "infrastructure_containers": sum(r["kind"] == "infrastructure" for r in inv),
        "containers_with_restarts": sum(int(r["restart_count"]) > 0 for r in inv),
        "observed_tcp_edges": len({(r["caller"], r["callee"]) for r in sockets}),
        "dependency_classifications": dict(Counter(r["classification"] for r in comparison)),
        "scenario_requests": len(scenario_rows), "scenario_failures": sum(s["failures"] for s in scenario_summary),
        "methodological_limits": [
            "Runtime connections are live TCP socket observations, not HTTP request counts.",
            "A missing edge means NOT_EXERCISED/NOT_OBSERVED under this workload, not unused.",
            "Scenario latency is gateway-observed end-to-end latency, not per-service span latency.",
            "Spring startup duration is available only when a matching startup log remains available.",
        ],
    }
    (output / "dynamic-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
