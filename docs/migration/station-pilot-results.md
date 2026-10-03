# Station pilot: implementation and validation

Date: 2026-09-29. Repository baseline: `35191344` plus the uncommitted migration
files in this workspace. Scope: port Station and validate coexistence with the
remaining running microservices.

## Result

**Station runs as the first module inside `ts-modulith`.** The existing UI and
microservices reach it through the old `ts-station-service:12345` identity. An
NGINX compatibility proxy holds the original Docker IP (`172.18.0.35`) so existing
DNS caches continue to work. The final routing mode is `module`.

The original Station container is retained, stopped and disconnected from the
application network. Its automatic restart is disabled while routing is installed;
the recovery script restores its previous policy. The separate legacy rollback
backend is also stopped. Only the module handles authoritative Station writes.
The original MongoDB database, collection and 13 station records are retained.

## Prechecks and baseline repairs

| Check | Finding/action |
| --- | --- |
| Repository | Original source/deployment files left intact; new host and migration tooling added |
| Docker | Available; existing application network and service identities inspected |
| Databases | Existing stopped MongoDB/MySQL/Redis containers restarted with their original volumes; no volume recreation |
| Source versus images | Running images are `codewisdom/*:0.2.0`; Station uses Boot 1.5.22/MongoDB. Checkout uses Boot 2.3.12/MySQL/Nacos |
| Runtime routing | Deployed UI NGINX routes directly to services; Java callers use legacy Docker service identities. The source gateway configuration is not the running ingress |
| Station data | Existing collection contains 13 stations; archive backup saved before cutover |
| Java/Maven | Host build succeeds with local JDK 21/Maven 3.9.9; produces Java 8 bytecode and runs in a pinned Java 8 container |
| Application health | 33 legacy Java services reported health UP after database restoration; four have pre-existing messaging-related problems |
| Non-Java probes | UI and News roots returned 200. Voucher, Avatar and Ticket Office root routes return 404; this does not establish those services are unhealthy and is not a functional test |

The earlier migration plan remains a source-level proposal. This pilot corrects
its routing/database assumptions for the actual deployed release. It does not
claim the MySQL source services have been validated against this Mongo deployment.

## Implemented boundary

- Independent host POM and one application bootstrap on Boot 2.3.12.
- Public `station.StationOperations`, Station DTO and response envelope.
- Private Station application logic, controller, storage interface and Mongo adapter.
- Architecture checks prevent dependencies on Station internals and persistence
  types in the public API, and reject module cycles.
- No Nacos registration, legacy bootstrap scanning, automatic data seeding or
  implicit database migration in the host.
- Existing JWT role conventions and administrative access rules retained.
- Candidate writes are disabled until the routing script enables module ownership.
- Reversible per-service proxy, maintenance window, readiness checks, and original
  container restoration. State is stored outside the Maven build directory.

This is a modular monolith architecture. Spring Modulith framework adoption and
the associated Boot upgrade remain separate work. Because the deployed baseline
uses Boot 1.5 and the host uses Boot 2.3, this pilot alone cannot isolate framework
effects from architecture effects in a performance experiment.

## Compatibility decisions

The running Station contract is the migration target:

| Behaviour | Running release / module | Newer checkout |
| --- | --- | --- |
| Persistence | MongoDB `ts.station`, legacy class marker | MySQL/JPA |
| Name handling | Preserve case and spaces | Remove spaces and lowercase |
| Duplicate create | Check Station ID | Check name |
| Batch names to IDs | Ordered list with `Not Exist` entries | Map from names to IDs |
| Delete | DELETE `/stations` with JSON body | DELETE `/stations/{id}` |

Mongo string and ObjectId representations are preserved, including Spring Data's
conversion of valid hexadecimal IDs. This prevents new records from becoming
unreadable by the old service after rollback.

One deliberate correction: malformed JWTs return **401**, while the old image
returns **500** because its token exception is not handled. The contract report
records this difference explicitly. Permission-denied checks compare status codes;
framework-generated error envelopes/timestamps are not claimed to be identical.

## Validation results

| Validation | Result |
| --- | --- |
| Maven package | Passed |
| Contract/unit and architecture tests | 9 passed, 0 failed |
| Differential checks with isolated legacy/module databases | 32 passed, including the explicit invalid-JWT exception |
| Live candidate | All 13 stations matched; authenticated writes rejected while read-only |
| Existing caller baseline | 9 passed |
| Proxy in legacy mode | Same 9 caller results as baseline |
| Module cutover | Same 9 caller results as baseline |
| Original-container restoration | Same 9 caller results as baseline |
| Final module deployment | Same 9 caller results as baseline |
| Write continuity | Admin created a record in module mode; legacy read and updated it; module read the update and deleted the fixture |

The nine caller checks cover direct Station, Station through UI NGINX, Basic,
Admin Basic Info, Admin through UI, Travel search, Travel2 search, Travel through
UI, and Orders refresh (station name mapping). They use running services and
databases, not mocks. Order Other had no seeded orders for the refresh scenario;
that path is not claimed as covered. Neither are all eight source-level callers.

Latency values in the smoke reports are diagnostic single-run timings, not
benchmarks or evidence of a performance improvement. Concurrent booking, payment,
refund, queue delivery, failure-load behaviour and production readiness remain
outside the validated Station slice.

## Remaining baseline failures

Preserve, Preserve Other and Food return health 503; Notification's health probe
times out. Their logs show RabbitMQ connection failures, including attempts to
reach `localhost:5672`. These predate the Station migration. Merely starting a
broker under a Docker alias would not fix clients configured for localhost.

The next baseline repair is to configure those services against a working local
broker and an isolated email sink, then validate full booking/cancellation flows.
No outbound notification test was performed. Do this before treating the stack as
a healthy baseline for migrating Orders or making end-to-end performance claims.

## Files and recovery

- [Host and operating runbook](../../ts-modulith/README.md)
- [Isolated/live deployment](../../deployment/migration/compose.station.yml)
- [Routing switch and recovery](station_routing.py)
- [Differential tests](verify_station.py)
- [Real-caller checks](verify_hybrid.py)
- [Write-continuity rehearsal](verify_cutover.py)
- [Runtime inventory](preflight.py)

Raw local evidence: `ts-modulith/target/evidence/` (inventory, contract reports,
caller baseline/module/rollback/final reports, fixture audit and Station archive).
Runtime routing state: `deployment/migration/.state/`. Preserve evidence before
Maven clean. Do not use root Compose to restart Station while the proxy owns its
network identity; use the migration script.

Rollback from the repository root:

```powershell
python docs/migration/station_routing.py legacy
```

Fully restore the original Station container and remove the proxy:

```powershell
python docs/migration/station_routing.py restore
```

These operations intentionally include a short maintenance window. Database
schema changes would require a new rollback plan; none were made in this pilot.
