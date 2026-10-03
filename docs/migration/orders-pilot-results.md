# Stage 2 checkpoint: Orders joins Station

Date: 29 September 2026. This is a tested local development checkpoint, not final
acceptance of the whole migration or a production readiness claim.

## Result

Station and Orders run in `station-migration-modulith-1`. Both live compatibility
routers point to the module. Other business services remain deployed separately.
Orders calls the exported Station API in-process. Each module owns its Mongo
access; existing databases, collections and identifiers are retained.

The running legacy release is `codewisdom/*:0.2.0`, using MongoDB and direct Docker
DNS. The checkout contains newer MySQL/Nacos implementations. Orders contracts and
implementation were recovered from the deployed legacy JAR for compatibility;
they were not copied from the incompatible newer implementation. The host uses
Boot 2.3.12 and Java 8; legacy uses Boot 1.5. Framework differences confound any
future architecture performance comparison. Spring Modulith framework adoption is
still deferred; module boundaries are currently checked with ArchUnit.

## Changes

- Ported Orders endpoints, DTOs and business logic, including legacy numeric JSON
  dates, UUID BSON subtype 3 encoding and the `order.entity.Order` class marker.
- Replaced Orders-to-Station HTTP with the exported `StationOperations` API.
- Added independent per-module write ownership. Rolling Orders back disables its
  writes without stopping Station. Legacy GET endpoints that mutate Orders are
  also gated. The legacy backend is stopped before granting module ownership.
- Retained original service IPs/aliases behind compatibility proxies so existing
  callers continue reaching the same addresses. Original containers are retained.
- Restored local RabbitMQ connectivity for Preserve, PreserveOther, Food and
  Notification, supplied Notification MongoDB, and routed SMTP to local Mailpit.
  Original Notification templates were restored after correcting the test payload.
- Added an existing-stack launcher, differential tests, booking workflow tests and
  checkpoint/rollback checks. See [testing instructions](TESTING.md).

## Validation completed

| Check | Result |
| --- | --- |
| Maven unit/architecture suite | 13 tests passed |
| Station legacy/module comparison on current image | 32 checks passed |
| Orders legacy/module comparison | 33 checks passed |
| Read-only Orders candidate against live data | Matched; mutation rejected |
| Legacy baseline booking/payment/cancellation | Passed |
| Module booking/payment/cancellation | Passed |
| Legacy rollback booking/payment/cancellation | Passed |
| Wallet debit and quoted refund invariants | Passed in all three workflows |
| Legacy reads module-created order | Passed |
| Module reads rollback-created order | Passed after returning to module |
| Station remains active during Orders rollback | Passed |
| Disabled Orders module rejects mutation with 503 | Passed; record unchanged |
| Local notification delivery with deployed DTO | Passed; message captured in Mailpit |
| Launcher and final module checkpoint | Passed |

No test used an existing person's account. Synthetic orders remain cancelled for
audit; their test wallet retains the corresponding cancellation fees. SMTP delivery
was verified directly with Notification; automatic booking-email delivery has not
been established by this check.

## Evidence and runtime state

- Source entry point: `ts-modulith/src/main/java/trainticket/ModulithApplication.java`.
- Current image: `train-ticket/ts-modulith:orders-pilot`, local image ID
  `sha256:ca6596b442326de26502724b15c2179eae3cb5bd1a65c804347a55213df41aec`.
- Ignored runtime state: `deployment/migration/.state/`, including independent
  routing states, ownership JSON, saved configuration and synthetic credentials.
- Ignored reports/backups: `ts-modulith/target/evidence/`, including
  `orders-contracts.json`, booking baseline/module/rollback reports,
  `checkpoint-legacy.json`, `checkpoint-module.json`, and Mongo archives.
- The original Notification JAR backup remains under ignored messaging state.
  The temporary template patch was undone; no template repair is required.

## Continue tomorrow

1. Run the launcher and checkpoint from TESTING.md. Review any failed checks before
   changing another service. Keep both modules routed to the host at this checkpoint.
2. Complete remaining Orders acceptance tests: duplicate/retried payments,
   concurrent seat allocation, failure recovery and controlled performance runs.
   These have not been validated by the sequential happy-path workflows.
3. Port OrderOther using its deployed contract and isolated Mongo snapshot. Reuse
   the Station API, ownership gate and independent router. Compare old/new contracts
   before live cutover, then test its real callers and rollback with post-cutover data.
4. Continue Config, Seat and Security according to the context map and migration
   plan. Revisit ordering when runtime coupling or test evidence changes the risk.

Do not retire legacy services or claim measured performance improvement yet.
The complete application migration, full browser coverage, concurrent/failure
scenarios and the methodology's controlled performance study remain outstanding.
