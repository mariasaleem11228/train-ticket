# Config migration checkpoint

Historical fourth-module checkpoint from 30 September 2026. The newer
[Seat checkpoint](seat-results.md) supersedes the running-state details below.
Config was the fourth Spring Modulith module in the shared
Spring Boot 3.5.16 / Java 21 host. Station, Orders and OrderOther remain routed
to the same host. Other business services continue as microservices.

## What changed

- The `trainticket.config` package declares a Spring Modulith module. Its public
  `ConfigOperations` API and JSON DTO are separate from its internal controller,
  service and MongoDB repository. The module has no dependency on another
  business module; Seat can consume its public API after Seat is migrated.
- The port follows the deployed `codewisdom/ts-config-service:0.2.0` MongoDB
  implementation, which differs from this checkout's MySQL/Nacos source. It
  keeps the `/api/v1/configservice` routes, response messages, HTTP 201 create
  status, `ts.config` collection, name-based IDs and legacy `_class` marker.
- The module does not run the legacy startup seeder. It reads the existing
  `DirectTicketAllocationProportion` record from Config's original MongoDB.
  Its independent write gate rejects writes whenever Config routes to legacy.
- A compatibility proxy holds the old `ts-config-service:15679` address. Port
  8080 also reaches it, with `X-Config-Backend: module` confirming the route.
  `python docs/migration/hybrid_routing.py legacy config` rolls back Config
  alone; `module config` returns it to the host.

## Evidence

- A MongoDB archive of the live `config` collection is preserved at ignored
  `ts-modulith/target/evidence/config-backup.archive` (one original document).
- The isolated deployed-versus-module comparison passed **20 checks**:
  baseline reads, welcome, missing data, create, duplicate, update, delete,
  final equality and rejection of writes by a read-only live candidate.
- The four-module Maven build passed **20 tests**, including Spring Modulith's
  `ApplicationModules.verify()` and ArchUnit checks for Config's boundary.
- The three existing routes and retained booking records passed the checkpoint
  after the shared-host upgrade. Config passed the checkpoint first in legacy
  router mode and again in module mode. `/actuator/modulith` reports four
  business modules.
- A Config-only rollback rehearsal passed: legacy read a module-created record,
  the inactive module rejected writes, legacy updated the record, and the module
  read that update after switching back. The disposable record was removed.

The running image is `train-ticket/ts-modulith:config-candidate`
(`sha256:97c27b2587784609b2b8ff560c78ef0f7097b2615e7773932e2d5eff7eb2029b`).
Routing and write ownership live under ignored `deployment/migration/.state/`;
preserve that directory and the original MongoDB volumes.

## Continue

Run `python docs/migration/run_hybrid.py`, then
`python docs/migration/verify_checkpoint.py`. For isolated comparisons, run
`python docs/migration/run_hybrid.py --comparisons` followed by
`python docs/migration/verify_config.py`. See [the testing guide](TESTING.md).
Seat is next in the [migration sequence](migration-plan.md). The Config result
does not establish performance improvement or complete migration.
