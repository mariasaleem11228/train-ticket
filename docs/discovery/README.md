# Automated architecture discovery

This directory contains a reproducible static inventory of the TrainTicket
microservice baseline. It does not perform or authorize any migration.

The thesis-ready account of the method, verification, findings and limitations
is [`static-analysis-report.md`](static-analysis-report.md). Generated CSV and
JSON files are the supporting appendices; inferred boundaries remain explicitly
separate from observed results.

## 1. Generate the inventory

From the repository root, with Python 3.9 or newer:

```powershell
python .\tools\architecture_inventory.py
```

The command reads production source, Maven descriptors, application
configuration, and `docker-compose.yml`. It writes replaceable artifacts under
`docs/discovery/generated/` and requires no third-party Python packages.

Run it again whenever the source or configuration changes. The generated files
are deterministic apart from their input fingerprint.

## 2. Check extraction quality

Open `generated/inventory-summary.json` first. Then apply these gates:

1. Every Compose component appears in `service-catalog.csv`.
2. Every reactor child appears in the catalog. The current root POM has 42
   children, or 43 reactor projects when the root aggregator is included.
3. Every production controller appears in `endpoints.csv`.
4. Every literal `http://ts-...` production URL appears in
   `http-dependencies.csv`.
5. Rows marked `UNKNOWN`, `Unresolved`, `image-only/infrastructure`, or
   `INFERRED_REQUIRES_REVIEW` are treated as explicit research gaps.

Useful independent checks:

```powershell
rg -n --glob '!**/target/**' --glob '*.java' '@(RestController|Controller)'
rg -n --glob '!**/target/**' --glob '*.java' 'http://ts-|getServiceUrl'
rg -n --glob '!**/target/**' --glob '*.java' '@(Entity|Document)|JpaRepository|MongoRepository'
```

Counts do not have to equal CSV row counts: one controller can expose many
endpoints, and one call expression can be dynamic. Differences must be explained.

## 3. Analyze the observed results

Use these files as observations:

- `service-catalog.csv`: deployment/build component coverage and technology.
- `endpoints.csv`: externally callable API surface.
- `http-dependencies.csv`: individual production call-site evidence.
- `callers-callees.csv`: fan-in and fan-out per service.
- `data-ownership.csv`: configured stores, persistent entities and repositories.
- `deployment-datastores.csv`: databases provisioned by Compose. Candidate
  ownership inferred from container naming is kept separate from source facts.
- `duplicated-types.csv`: same-named Java types across module boundaries.
- `dependency-matrix.csv` and `dependency-graph.mmd`: service-level coupling.

Interpret fan-in as migration risk: a high fan-in service has many consumers.
Interpret fan-out as orchestration responsibility: a high fan-out service may be
an application coordinator rather than a cohesive domain module. Reciprocal
edges and services sharing duplicated domain types are candidates for closer
inspection. Shared data vocabulary alone is not sufficient evidence to merge.

Render `dependency-graph.mmd` with a Mermaid-capable Markdown editor or Mermaid
CLI. The CSV matrix can be imported into Excel for filtering or heat-map
formatting.

## 4. Analyze the hypotheses separately

`candidate-contexts.csv` and `candidate-migration-order.csv` are deliberately
marked `INFERRED_REQUIRES_REVIEW`. The context assignment uses service-name
keywords. The order initially places services with lower observed static HTTP
degree first. Neither file is an architectural decision.

For each proposed context, validate:

1. Does it own one coherent business capability?
2. Can its data be owned without cross-module table access?
3. Are calls inside the candidate context more frequent than calls outside it?
4. Are duplicated types genuinely the same concept and lifecycle?
5. Can its public API be expressed as Java module interfaces later?
6. Are image-only services or unresolved dynamic calls hiding dependencies?

Record accepted, rejected, and changed assignments in a separate reviewed
document. Do not edit the generated CSV to hide uncertainty.

## 5. Architecture review gate

Do not begin merging services until:

- catalog coverage is complete;
- unresolved production calls have been investigated;
- database ownership is known or explicitly documented as unknown;
- proposed contexts have written evidence and counter-evidence;
- the migration order considers runtime criticality and tests in addition to
  static coupling;
- a supervisor or architecture review has approved the module boundaries.

Static analysis cannot observe calls made only inside unavailable prebuilt
images or all values assembled dynamically at runtime. A later runtime phase
should correlate this inventory with gateway access logs or tracing, but that is
an extension of discovery, not a reason to start merging early.
