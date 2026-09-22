#!/usr/bin/env python3
"""Generate an evidence-backed static architecture inventory for TrainTicket.

Uses only the Python standard library. Generated facts include file/line evidence.
Heuristic architectural suggestions are written separately from observed facts.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path


HTTP_ANNOTATIONS = {
    "GetMapping": "GET", "PostMapping": "POST", "PutMapping": "PUT",
    "DeleteMapping": "DELETE", "PatchMapping": "PATCH", "RequestMapping": "ANY",
}
CONTEXT_RULES = [
    ("Administration", ("admin",)),
    ("Consignment", ("consign",)),
    ("Food and delivery", ("food", "delivery")),
    ("Identity and customer", ("auth", "user", "contacts", "verification", "security", "avatar")),
    ("Rail network and timetable", ("station", "train", "route", "travel", "basic", "price", "seat", "plan")),
    ("Booking and order lifecycle", ("preserve", "order", "cancel", "rebook", "execute", "wait")),
    ("Payment and assurance", ("payment", "assurance", "voucher")),
    ("Customer communication", ("notification", "news")),
    ("Edge and presentation", ("gateway", "ui-dashboard")),
]


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def evidence(root: Path, path: Path, line: int) -> str:
    return f"{rel(root, path)}:{line}"


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def reactor_modules(root: Path) -> list[str]:
    text = read(root / "pom.xml")
    return re.findall(r"<module>\s*([^<]+?)\s*</module>", text)


def module_evidence(root: Path) -> dict[str, str]:
    path = root / "pom.xml"
    text = read(path)
    return {m.group(1).strip(): evidence(root, path, line_number(text, m.start()))
            for m in re.finditer(r"<module>\s*([^<]+?)\s*</module>", text)}


def parse_compose(root: Path) -> dict[str, dict]:
    """Parse the simple top-level service blocks without requiring PyYAML."""
    path = root / "docker-compose.yml"
    lines = read(path).splitlines()
    result: dict[str, dict] = {}
    in_services = False
    current = None
    for no, raw in enumerate(lines, 1):
        if raw.strip() == "services:":
            in_services = True
            continue
        if in_services and raw and not raw.startswith(" ") and not raw.lstrip().startswith("#"):
            break
        service_match = re.match(r"^  ([A-Za-z0-9_.-]+):\s*$", raw)
        if in_services and service_match:
            current = service_match.group(1)
            result[current] = {"compose_evidence": evidence(root, path, no), "images": [], "builds": [], "ports": []}
            continue
        if not current or raw.lstrip().startswith("#"):
            continue
        m = re.match(r"^\s{4,}(image|build):\s*['\"]?([^'\"#]+?)['\"]?\s*$", raw)
        if m:
            result[current][m.group(1) + "s"].append(m.group(2).strip())
        p = re.match(r"^\s+-\s*['\"]?(\d+)\s*:\s*(\d+)['\"]?", raw)
        if p:
            result[current]["ports"].append(f"{p.group(1)}:{p.group(2)}")
    return result


def pom_facts(module_dir: Path) -> tuple[str, list[str]]:
    pom = module_dir / "pom.xml"
    if not pom.exists():
        return "", []
    try:
        root = ET.parse(pom).getroot()
        ns = {"m": "http://maven.apache.org/POM/4.0.0"}
        artifact = root.findtext("m:artifactId", default="", namespaces=ns)
        deps = [x.text or "" for x in root.findall(".//m:dependency/m:artifactId", ns)]
        return artifact, deps
    except ET.ParseError:
        text = read(pom)
        return "", re.findall(r"<artifactId>([^<]+)</artifactId>", text)


def technologies(deps: list[str], files: list[Path]) -> list[str]:
    values = []
    joined = " ".join(deps)
    checks = [
        ("Spring Boot", "spring-boot"), ("Spring MVC", "starter-web"),
        ("Spring Data JPA", "data-jpa"), ("Spring Data MongoDB", "data-mongodb"),
        ("MySQL", "mysql-connector"), ("Nacos discovery", "nacos-discovery"),
        ("Redis", "data-redis"), ("RabbitMQ", "starter-amqp"), ("Kafka", "kafka"),
    ]
    for label, token in checks:
        if token in joined:
            values.append(label)
    if any(p.suffix == ".java" for p in files):
        values.insert(0, "Java")
    return values


def annotation_value(args: str) -> str:
    strings = re.findall(r'"([^"\n]*)"', args)
    return strings[0] if strings else ""


def join_path(base: str, child: str) -> str:
    parts = [p.strip("/") for p in (base, child) if p.strip("/")]
    return "/" + "/".join(parts) if parts else "/"


def scan_endpoints(root: Path, module: str, files: list[Path]) -> list[dict]:
    rows = []
    pattern = re.compile(r"@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\s*(?:\((.*?)\))?", re.S)
    for path in files:
        text = read(path)
        if "@RestController" not in text and "@Controller" not in text:
            continue
        class_pos = min([x for x in (text.find(" class "), text.find(" interface ")) if x >= 0] or [len(text)])
        base = ""
        for m in pattern.finditer(text[:class_pos]):
            if m.group(1) == "RequestMapping":
                base = annotation_value(m.group(2) or "")
        for m in pattern.finditer(text[class_pos:]):
            absolute = class_pos + m.start()
            name, args = m.group(1), m.group(2) or ""
            method = HTTP_ANNOTATIONS[name]
            if name == "RequestMapping":
                method_match = re.search(r"RequestMethod\.(GET|POST|PUT|DELETE|PATCH)", args)
                if not method_match:
                    continue
                method = method_match.group(1)
            rows.append({"service": module, "http_method": method,
                         "path": join_path(base, annotation_value(args)),
                         "controller": path.stem,
                         "evidence": evidence(root, path, line_number(text, absolute))})
    return rows


def scan_http(root: Path, module: str, files: list[Path]) -> list[dict]:
    rows, seen = [], set()
    # Captures literal service URLs. Dynamic service-name construction is reported separately.
    url_re = re.compile(r'https?://(ts-[A-Za-z0-9_-]+)(?::(\d+))?([^"\s]*)')
    for path in files:
        text = read(path)
        if "src/main/" not in path.as_posix():
            continue
        def infer_method(pos: int) -> str:
            window = text[max(0, pos - 150):min(len(text), pos + 900)]
            methods = re.findall(r"HttpMethod\.(GET|POST|PUT|DELETE|PATCH)", window)
            if methods:
                return methods[0]
            calls = re.findall(r"\.((?:get|post|put|delete|patch)For(?:Object|Entity))\s*\(", window, re.I)
            return re.match(r"[A-Za-z]+", calls[0]).group(0).replace("ForObject", "").replace("ForEntity", "").upper() if calls else "UNKNOWN"

        for m in url_re.finditer(text):
            endpoint = m.group(3).rstrip(";,)") or "/"
            key = (module, m.group(1), endpoint, evidence(root, path, line_number(text, m.start())))
            if key in seen:
                continue
            seen.add(key)
            rows.append({"caller": module, "callee": m.group(1), "http_method": infer_method(m.start()),
                         "url_or_path": endpoint, "resolution": "literal URL",
                         "evidence": key[3]})
        assignments = {}
        for assignment in re.finditer(r'\b(?:String\s+)?(\w+)\s*=\s*getServiceUrl\(\s*"(ts-[A-Za-z0-9_-]+)"\s*\)', text):
            assignments[assignment.group(1)] = assignment.group(2)
        resolved_assignment_offsets = set()
        for variable, callee in assignments.items():
            usage_re = re.compile(r"\b" + re.escape(variable) + r'\s*\+\s*"([^"\n]+)"')
            for usage in usage_re.finditer(text):
                path_value = usage.group(1) if usage.group(1).startswith("/") else "/" + usage.group(1)
                ev = evidence(root, path, line_number(text, usage.start()))
                key = (module, callee, path_value, ev)
                if key not in seen:
                    seen.add(key)
                    resolved_assignment_offsets.add((callee, line_number(text, usage.start())))
                    rows.append({"caller": module, "callee": callee, "http_method": infer_method(usage.start()),
                                 "url_or_path": path_value, "resolution": "local URL-variable analysis",
                                 "evidence": ev})
        for m in re.finditer(r'getServiceUrl\(\s*"(ts-[A-Za-z0-9_-]+)"\s*\)', text):
            key = (module, m.group(1), "DYNAMIC", evidence(root, path, line_number(text, m.start())))
            # Keep unresolved declarations only when no path use was found for that callee.
            if key not in seen and not any(x[0] == m.group(1) for x in resolved_assignment_offsets):
                seen.add(key)
                rows.append({"caller": module, "callee": m.group(1), "http_method": "UNKNOWN",
                             "url_or_path": "constructed near call site", "resolution": "service-name expression",
                             "evidence": key[3]})
    return rows


def scan_data(root: Path, module: str, files: list[Path]) -> list[dict]:
    stores: defaultdict[str, list[tuple[str, str]]] = defaultdict(list)
    configs = list((root / module / "src/main/resources").glob("application.y*ml")) + list((root / module / "src/main/resources").glob("application.properties"))
    for path in configs:
        text = read(path)
        patterns = [
            (r"jdbc:mysql:[^\s#]+", "MySQL"),
            (r"mongodb(?:\+srv)?://[^\s#]+", "MongoDB"),
            (r"(?m)^\s*mongodb\s*:\s*(?:#.*)?$", "MongoDB"),
        ]
        for regex, store in patterns:
            for m in re.finditer(regex, text, re.I):
                current_line = text[text.rfind("\n", 0, m.start()) + 1:m.start()]
                if current_line.lstrip().startswith("#"):
                    continue
                value = m.group(0).strip() or "mongodb configuration section"
                item = (value, evidence(root, path, line_number(text, m.start())))
                if item not in stores[store]:
                    stores[store].append(item)
    entities = []
    repos = []
    for path in files:
        text = read(path)
        if re.search(r"@(Entity|Document)\b", text):
            m = re.search(r"\bclass\s+(\w+)", text)
            if m:
                entities.append((m.group(1), evidence(root, path, line_number(text, m.start()))))
        if re.search(r"extends\s+(JpaRepository|MongoRepository|CrudRepository)", text):
            m = re.search(r"\binterface\s+(\w+)", text)
            if m:
                repos.append((m.group(1), evidence(root, path, line_number(text, m.start()))))
    if not stores and (entities or repos):
        stores["Unresolved"].append(("persistence code found; configuration not resolved", (entities + repos)[0][1]))
    return [{"service": module, "store": store,
             "connection_evidence": "; ".join(value for value, _ in configurations),
             "entities": "; ".join(x[0] for x in entities),
             "repositories": "; ".join(x[0] for x in repos),
             "evidence": "; ".join(ev for _, ev in configurations) +
                         ("; " + "; ".join(x[1] for x in entities) if entities else "")}
            for store, configurations in stores.items()]


def context_for(name: str) -> str:
    lowered = name.lower()
    for context, tokens in CONTEXT_RULES:
        if any(token in lowered for token in tokens):
            return context
    return "Unclassified"


def responsibility_for(name: str, classification: str) -> str:
    phrase = name.removeprefix("ts-").removesuffix("-service").replace("-", " ")
    if classification == "database/infrastructure":
        return f"Supports persistence or infrastructure for {phrase}"
    if classification == "shared library":
        return "Provides Java types and utilities shared by service modules"
    if classification == "image-only/infrastructure":
        return f"Provides {phrase}; internals unavailable in local source"
    return f"Provides the {phrase} capability"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    root = args.root.resolve()
    out = (args.out or root / "docs" / "discovery" / "generated").resolve()
    out.mkdir(parents=True, exist_ok=True)

    modules = reactor_modules(root)
    module_lines = module_evidence(root)
    compose = parse_compose(root)
    source_modules = {m for m in modules if (root / m).is_dir()}
    components = sorted(set(compose) | source_modules)
    catalog, endpoints, calls, data = [], [], [], []
    type_locations: defaultdict[str, list[str]] = defaultdict(list)

    for name in components:
        directory = root / name
        java_files = list(directory.glob("src/main/**/*.java")) if directory.exists() else []
        artifact, deps = pom_facts(directory)
        c = compose.get(name, {})
        classification = "source-inspected service" if java_files else ("source module" if directory.exists() else "image-only/infrastructure")
        if name == "ts-common":
            classification = "shared library"
        if name.endswith(("-mongo", "-mysql")) or name in {"redis", "rabbitmq", "kafka", "zipkin"}:
            classification = "database/infrastructure"
        catalog.append({"component": name, "classification": classification, "reactor_module": name in modules,
                        "artifact": artifact, "image": "; ".join(c.get("images", [])),
                        "build_context": "; ".join(c.get("builds", [])), "ports": "; ".join(c.get("ports", [])),
                        "technology": "; ".join(technologies(deps, java_files)),
                        "uses_ts_common": "ts-common" in deps,
                        "responsibility_status": "INFERRED_FROM_NAME",
                        "business_responsibility": responsibility_for(name, classification),
                        "evidence": c.get("compose_evidence", "") or module_lines.get(name, "")})
        endpoints.extend(scan_endpoints(root, name, java_files))
        calls.extend(scan_http(root, name, java_files))
        data.extend(scan_data(root, name, java_files))
        for p in java_files:
            text = read(p)
            for m in re.finditer(r"\b(?:class|enum|interface)\s+(\w+)", text):
                type_locations[m.group(1)].append(evidence(root, p, line_number(text, m.start())))

    deployment_stores = []
    for component, details in sorted(compose.items()):
        store = ""
        suffix = ""
        if component.endswith("-mongo"):
            store, suffix = "MongoDB", "-mongo"
        elif component.endswith("-mysql"):
            store, suffix = "MySQL", "-mysql"
        if not store:
            continue
        owner_candidate = component[:-len(suffix)] + "-service"
        owner_status = "INFERRED_FROM_NAME" if owner_candidate in components else "UNRESOLVED"
        deployment_stores.append({"database_component": component, "store": store,
                                  "candidate_owner": owner_candidate if owner_status != "UNRESOLVED" else "",
                                  "owner_status": owner_status,
                                  "image": "; ".join(details.get("images", [])),
                                  "evidence": details.get("compose_evidence", "")})

    # Call counts and matrix use unique service-level edges.
    edges = sorted(set((x["caller"], x["callee"]) for x in calls))
    incoming, outgoing = Counter(b for a, b in edges), Counter(a for a, b in edges)
    callers = defaultdict(list)
    callees = defaultdict(list)
    for a, b in edges:
        callees[a].append(b); callers[b].append(a)
    call_summary = [{"service": n, "callers": "; ".join(sorted(callers[n])), "callees": "; ".join(sorted(callees[n])),
                     "in_degree": incoming[n], "out_degree": outgoing[n]} for n in sorted(set(source_modules) | set(callers) | set(callees))]

    matrix_nodes = sorted(set(a for a, _ in edges) | set(b for _, b in edges))
    matrix_rows = []
    edge_set = set(edges)
    for a in matrix_nodes:
        row = {"caller\\callee": a}
        row.update({b: 1 if (a, b) in edge_set else 0 for b in matrix_nodes})
        matrix_rows.append(row)

    duplicates = [{"type_name": name, "occurrences": len(locations), "evidence": "; ".join(locations)}
                  for name, locations in sorted(type_locations.items())
                  if len({x.split("/", 1)[0] for x in locations}) > 1]
    domain_services = source_modules - {"ts-common"}
    hypotheses = [{"service": n, "candidate_context": context_for(n),
                   "candidate_module": re.sub(r"[^a-z0-9]+", "-", context_for(n).lower()).strip("-"),
                   "basis": "service-name keyword heuristic",
                   "status": "INFERRED_REQUIRES_REVIEW"} for n in sorted(domain_services)]
    # Low coupling is a safe first extraction candidate, but business/data review still controls final order.
    migration_candidates = source_modules - {"ts-common", "ts-gateway-service"}
    migration = sorted(migration_candidates, key=lambda n: (incoming[n] + outgoing[n], outgoing[n], n))
    migration_rows = [{"candidate_rank": i + 1, "service": n, "candidate_context": context_for(n),
                       "observed_degree": incoming[n] + outgoing[n], "rationale": "lower observed static HTTP coupling first",
                       "status": "INFERRED_REQUIRES_REVIEW"} for i, n in enumerate(migration)]

    write_csv(out / "service-catalog.csv", catalog, list(catalog[0]))
    write_csv(out / "endpoints.csv", endpoints, ["service", "http_method", "path", "controller", "evidence"])
    write_csv(out / "http-dependencies.csv", calls, ["caller", "callee", "http_method", "url_or_path", "resolution", "evidence"])
    write_csv(out / "callers-callees.csv", call_summary, ["service", "callers", "callees", "in_degree", "out_degree"])
    write_csv(out / "data-ownership.csv", data, ["service", "store", "connection_evidence", "entities", "repositories", "evidence"])
    write_csv(out / "deployment-datastores.csv", deployment_stores,
              ["database_component", "store", "candidate_owner", "owner_status", "image", "evidence"])
    write_csv(out / "duplicated-types.csv", duplicates, ["type_name", "occurrences", "evidence"])
    write_csv(out / "dependency-matrix.csv", matrix_rows, ["caller\\callee"] + matrix_nodes)
    write_csv(out / "candidate-contexts.csv", hypotheses, ["service", "candidate_context", "candidate_module", "basis", "status"])
    write_csv(out / "candidate-migration-order.csv", migration_rows, ["candidate_rank", "service", "candidate_context", "observed_degree", "rationale", "status"])

    graph = ["flowchart LR"]
    for a, b in edges:
        graph.append(f'  {re.sub("[^A-Za-z0-9_]", "_", a)}["{a}"] --> {re.sub("[^A-Za-z0-9_]", "_", b)}["{b}"]')
    (out / "dependency-graph.mmd").write_text("\n".join(graph) + "\n", encoding="utf-8")
    summary = {"reactor_children": len(modules), "reactor_projects_including_root": len(modules) + 1,
               "compose_components": len(compose), "catalog_components": len(catalog),
               "endpoints": len(endpoints), "http_call_sites": len(calls), "unique_http_edges": len(edges),
               "source_data_ownership_rows": len(data), "compose_datastores": len(deployment_stores),
               "duplicated_type_names": len(duplicates),
               "limitations": ["Regex-based static analysis; dynamic URLs may require review.",
                               "Business responsibilities, contexts, modules, and migration order are hypotheses.",
                               "Runtime-discovered calls and image-only internals are not observable from local source."]}
    (out / "inventory-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    fingerprint = hashlib.sha256("\n".join(sorted(f"{p}:{p.stat().st_mtime_ns}" for p in root.glob("*/src/main/**/*") if p.is_file())).encode()).hexdigest()
    (out / "generation-metadata.json").write_text(json.dumps({"generator": rel(root, Path(__file__).resolve()), "input_fingerprint": fingerprint}, indent=2) + "\n", encoding="utf-8")
    unresolved = [x for x in calls if x["http_method"] == "UNKNOWN"]
    source_store_by_service = defaultdict(set)
    for row in data:
        source_store_by_service[row["service"]].add(row["store"])
    store_mismatches = [row for row in deployment_stores
                        if row["candidate_owner"] in source_store_by_service and
                        row["store"] not in source_store_by_service[row["candidate_owner"]]]
    mismatch_rows = [{"service": row["candidate_owner"],
                      "source_configured_stores": "; ".join(sorted(source_store_by_service[row["candidate_owner"]])),
                      "compose_store": row["store"], "database_component": row["database_component"],
                      "status": "OBSERVED_MISMATCH_REQUIRES_INVESTIGATION", "evidence": row["evidence"]}
                     for row in store_mismatches]
    write_csv(out / "source-compose-datastore-mismatches.csv", mismatch_rows,
              ["service", "source_configured_stores", "compose_store", "database_component", "status", "evidence"])
    quality = [
        {"check": "reactor modules catalogued", "result": "PASS" if all(m in components for m in modules) else "FAIL", "detail": f"{len(modules)} of {len(modules)} expected"},
        {"check": "compose components catalogued", "result": "PASS" if all(m in components for m in compose) else "FAIL", "detail": f"{len(compose)} of {len(compose)} expected"},
        {"check": "unresolved HTTP methods", "result": "REVIEW" if unresolved else "PASS", "detail": str(len(unresolved))},
        {"check": "image-only component internals", "result": "REVIEW", "detail": str(sum(x["classification"] == "image-only/infrastructure" for x in catalog))},
        {"check": "source/Compose datastore mismatches", "result": "REVIEW" if store_mismatches else "PASS", "detail": str(len(store_mismatches))},
        {"check": "inferred responsibilities and boundaries", "result": "REVIEW", "detail": "All require domain validation"},
    ]
    write_csv(out / "quality-report.csv", quality, ["check", "result", "detail"])
    print(json.dumps(summary, indent=2))
    print(f"Generated inventory: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
