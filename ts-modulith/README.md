# Train Ticket modular monolith

## Current checkpoint: Spring Modulith with twenty-two services

Station, Orders, OrderOther, Config, Seat, Security, Train, Route, Price, Basic, Travel, Travel2, Route Plan, Travel Plan, Contacts, Preserve, PreserveOther, Execute, Payment, Inside Payment, Cancel and Rebook run in one Spring Modulith 1.4.13 / Spring Boot 3.5.16 / Java 21
host. They are declared with `@ApplicationModule`; `@Modulithic` marks the
application, and the architecture test verifies their boundaries. Orders and
OrderOther each depend on Station's published API. Remaining business services
run as microservices.
Use the [current testing guide](../docs/migration/TESTING.md) and
[Rebook results and continuation checkpoint](../docs/migration/rebook-results.md).

```powershell
python docs/migration/run_hybrid.py
python docs/migration/verify_checkpoint.py
Invoke-RestMethod http://localhost:18080/actuator/modulith | ConvertTo-Json -Depth 8
```

Open http://localhost:8080. To start isolated legacy/module comparisons as well,
run `python docs/migration/run_hybrid.py --comparisons`.
Use `hybrid_routing.py legacy orderother` or `hybrid_routing.py module orderother`
for independent OrderOther rollback/cutover. The shared host keeps Station and Orders
running. A per-module ownership file gates writes.

Build the current image with `docker build -t train-ticket/ts-modulith:rebook-candidate ts-modulith`
after `mvn -f ts-modulith/pom.xml package` succeeds.

## Historical stage 1 instructions

The sections below describe the original Station-only stage, when Spring Modulith
had not yet been adopted. Its deployment and switch commands are superseded by
the current guide above for this workspace.

### Station migration pilot

One deployable Spring Boot application, with Station as the first business module.
The running local stack uses `codewisdom/*:0.2.0`, MongoDB and direct Docker DNS.
It does **not** match the checkout's newer MySQL/Nacos implementation. This pilot
targets the running release so its remaining microservices can continue calling
Station. The source-version differences are recorded in the migration report.

## Structure

```text
trainticket
  ModulithApplication       single bootstrap
  station                   exported API and DTOs, no Spring dependencies
    internal                controller, application service, persistence port/adapter
  security                  legacy JWT adapter and HTTP authorisation
```

Future modules may use `station.StationOperations`, never `station.internal`.
ArchUnit checks exported API dependencies, internal access and module cycles.
There is no in-process HTTP call. Mongo access belongs exclusively to Station.

The host uses Boot 2.3.12, matching the checkout's framework line, and Java 8
bytecode/runtime. It is a modular monolith architecture; adopting the Spring
Modulith framework is deferred because that requires a Boot upgrade. The standalone
POM avoids inheriting Nacos, Swagger, shared entity scanning and the root's old
JaCoCo plugin. The legacy image uses Boot 1.5, so comparisons with that image also
include a framework change. Do not attribute latency differences solely to architecture.

## Build and isolated contracts

From the repository root (PowerShell):

```powershell
mvn -f ts-modulith/pom.xml package
docker build -t train-ticket/ts-modulith:station-pilot ts-modulith
docker compose -p station-migration -f deployment/migration/compose.station.yml up -d station-test-mongo station-legacy-test station-module-test modulith
```

Before comparisons, snapshot the actual Station collection and restore it only into
the isolated module test database. The old test image seeds the benchmark's 13
stations. If the live dataset differs, make both test datasets identical first;
do not accept a failing comparison or silently filter application records.

The initial run used this existing database container (discover its name using
`docker ps` on another machine):

```powershell
New-Item -ItemType Directory -Force ts-modulith/target/evidence | Out-Null
docker exec cf53a5d827fe_train-ticket-ts-station-mongo-1 mongodump --db ts --collection station --archive=/tmp/station-migration-backup.archive
docker cp cf53a5d827fe_train-ticket-ts-station-mongo-1:/tmp/station-migration-backup.archive ts-modulith/target/evidence/station-backup.archive
docker cp ts-modulith/target/evidence/station-backup.archive station-migration-station-test-mongo-1:/tmp/station.archive
docker exec station-migration-station-test-mongo-1 mongorestore --archive=/tmp/station.archive --nsFrom=ts.station --nsTo=module.station
python docs/migration/verify_station.py
```

The differential suite uses ports **22345 and 18081 only**, backed by an isolated
Mongo container. It tests reads, batches, missing values, case/space preservation,
Unicode, duplicate IDs, CRUD, permissions and hexadecimal Mongo IDs. It generates
local benchmark JWTs; it does not test login or token issuance. It records one
intentional difference: invalid JWTs produce 401 rather than the legacy 500.

The live candidate is on `127.0.0.1:18080`. It uses the existing Station database,
performs no startup writes, and starts with `STATION_WRITES_ENABLED=false`.
Read-only batch POST endpoints remain available. Administrative writes return 503
until the routing script explicitly enables this instance as the writer.

## Preflight, cutover and rollback

```powershell
python docs/migration/preflight.py
python docs/migration/verify_hybrid.py baseline
python docs/migration/station_routing.py install
python docs/migration/station_routing.py module
python docs/migration/verify_hybrid.py module
```

`install` requires the isolated contract results and Station backup. It retains
the original container, moves its Docker network IP and service alias to an NGINX
proxy, and routes first to a separate legacy backend. Keeping the original IP
allows already-running JVMs and UI NGINX workers to keep using cached addresses.
The original container is stopped and disconnected, not deleted. No database
volume is recreated. The live Mongo database and collection remain unchanged.

`module` briefly puts the proxy into maintenance mode, stops the legacy backend,
starts the module with writes enabled, checks readiness, and switches the proxy.
`legacy` does the reverse and stops the module. During this development pilot,
switching has an intentional maintenance window; this is not a zero-downtime
production rollout. On a switch failure the script attempts to restore the original
container and reports any failure instead of claiming success.

```powershell
python docs/migration/station_routing.py legacy  # roll back via proxy
python docs/migration/station_routing.py module  # return to module
python docs/migration/station_routing.py status
python docs/migration/station_routing.py restore # remove proxy; restore original IP/name/port
```

For the write-continuity rehearsal, `verify_cutover.py create` creates one uniquely
named Station through the **existing Admin Basic Info service** in module mode.
After switching to legacy, `verify_cutover.py rollback` reads and updates it.
After switching to module again, `verify_cutover.py cleanup` verifies the update
and deletes only that fixture. Fixture state is retained for audit/recovery.

While routing is installed, manage these services with `station_routing.py`.
Running the root Compose deployment or starting the original Station manually
can conflict with the proxy's port/network ownership. Do not run plain migration
Compose `up` on the active module: its default write setting is intentionally false.

Runtime routing state/configuration lives under ignored
`deployment/migration/.state/` so Maven clean cannot remove the active proxy config.
Test evidence and backups are under `ts-modulith/target/evidence/`; preserve them
before cleaning builds. The source runbook and summary report are checked-in files.

## Contracts and limits

Payment is included as an independent Spring Modulith module. Its live compatibility endpoint is `ts-payment-service:19001`; `X-Payment-Backend: module` confirms the proxy target. See [Payment results](../docs/migration/payment-results.md) for the contract comparison, rollback rehearsal, and test commands.

- Existing API prefix: `/api/v1/stationservice`.
- Existing externally visible service name/port: `ts-station-service:12345`.
- POST/PUT/DELETE of `/stations` require `ROLE_ADMIN`; lookups remain public.
- DELETE accepts a Station JSON body. Name-to-ID batches return ordered lists,
  including `Not Exist` placeholders; they are not maps.
- Mongo `_id`, collection `station`, database `ts`, and the legacy `_class` marker
  are preserved. No schema, data model, broker or identity migration is included.
- `/actuator/health` on the host checks Mongo connectivity. The proxy adds
  `X-Station-Backend` so tests can verify which implementation served a request.
- RabbitMQ-related baseline failures in other services are recorded separately.
  Passing Station/search checks does not establish complete booking/payment health.
- Existing benchmark JWT signing conventions are retained for interoperability.
  This is a local migration experiment, not a production security upgrade.
