"""Reproduce the static Java service-reference inventory. Run from any directory.

This is a heuristic source scan, not a runtime call graph. Gateway configuration,
brokers, non-Java callers and dynamically assembled names require separate review.
"""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
services = sorted(p.name for p in ROOT.glob('ts-*-service') if p.is_dir())
evidence = []
edges = {name: set() for name in services}
for name in services:
    for path in sorted((ROOT / name / 'src/main').rglob('*.java')):
        source = path.read_text(encoding='utf-8', errors='replace')
        # Preserve line numbers while removing block comments.
        source = re.sub(r'/\*.*?\*/', lambda m: '\n' * m[0].count('\n'), source, flags=re.S)
        for number, line in enumerate(source.splitlines(), 1):
            if line.lstrip().startswith('//'):
                continue
            for target in sorted(set(re.findall(r'\bts-[a-z0-9-]+-service\b', line))):
                if target != name:
                    edges[name].add(target)
                    evidence.append((name, target, path.relative_to(ROOT).as_posix(), number))

with (OUT / 'dependency-evidence.csv').open('w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['caller', 'provider', 'source', 'line'])
    writer.writerows(evidence)

with (OUT / 'service-dependencies.csv').open('w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(['service', 'java_source_present', 'distinct_java_callers', 'distinct_java_providers', 'providers'])
    for name in sorted(services, key=lambda n: (-sum(n in targets for targets in edges.values()), n)):
        writer.writerow([name, (ROOT / name / 'src/main/java').is_dir(),
                         sum(name in targets for targets in edges.values()),
                         len(edges[name]), ';'.join(sorted(edges[name]))])

lines = ['flowchart LR']
for name in services:
    if (ROOT / name / 'src/main/java').is_dir():
        lines.append(f'  {name.replace("-", "_")}["{name}"]')
for caller, targets in sorted(edges.items()):
    for target in sorted(targets):
        lines.append(f'  {caller.replace("-", "_")} --> {target.replace("-", "_")}')
(OUT / 'java-service-graph.mmd').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(f'Wrote inventory, evidence and graph: {sum(map(len, edges.values()))} distinct Java reference edges.')
