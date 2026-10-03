# Stage 3 checkpoint: OrderOther joins the modulith

Historical stage-3 snapshot from 30 September 2026, before the
[Spring Modulith framework upgrade](spring-modulith-results.md). Station, Orders
and OrderOther share one host.
Other services remain microservices. This is a local development checkpoint;
the full migration and performance study remain outstanding.

## Behavior and compatibility

OrderOther was ported from the deployed `codewisdom/ts-order-other-service:0.2.0`
JAR, since the checkout's newer MySQL/Nacos source differs from the running
MongoDB release. Its controller, DTOs and application logic preserve the deployed
paths and response messages. OrderOther owns the existing `ts.orders` collection
in its separate Mongo instance, including BSON legacy UUID encoding and the
`other.entity.Order` class marker. Station name refresh uses the exported in-process
Station API. The module does not seed an order on startup.

The module rejects anonymous order creation and USER-role admin creation with 403.
The deployed service accepts both. These are two intentional security corrections
in the comparison results; normal authenticated booking is unaffected.

## Validation

| Check | Result |
| --- | --- |
| Maven unit/architecture suite | 16 tests passed |
| Isolated deployed/module comparison | 31/31 checks passed, including two documented authorization differences |
| Read-only candidate against live two-record database | Reads and refresh matched; mutation returned 503 |
| Module-created order read and updated by rollback backend | Passed |
| Legacy-updated order read and deleted by module | Passed |
| Real Travel2 → PreserveOther → OrderOther booking | Passed |
| Wallet debit, payment, cancellation and quoted refund | Passed |
| Browser port 8080 route and `X-OrderOther-Backend: module` | Passed |
| Shared host health and Station/Orders regression checkpoint | Passed |

The deployed legacy OrderOther JAR creates a sample order on every startup. The
first router startup created one extra sample; it was identified against the
pre-cutover two-record backup, deleted, and the original IDs were verified. Future
rollbacks and isolated legacy comparisons use a locally built image with only its
`InitData.class` removed.
The build script verifies that every other JAR entry is byte-for-byte identical.
After the rollback rehearsal and fixture cleanup, the live collection again held
exactly the original two records. The real booking test then added one cancelled
synthetic order, retained for audit in the fixture state.

## Evidence and next service

- Host image at this stage: `train-ticket/ts-modulith:order-other-pilot`, local image ID
  `sha256:046c304f71fd1e7434d5cce6c12ccf184a5da0aea131e93366dff00805a40ea5`.
- Original OrderOther archive and comparison reports are under ignored
  `ts-modulith/target/evidence/`.
- Router and writer ownership state are under ignored
  `deployment/migration/.state/`; preserve them across Docker restarts.
- [Test and rollback commands](TESTING.md) resume this same hybrid deployment.

Next in the context-map sequence is Config, then Seat and Security. Before retiring
any legacy service or drawing architecture performance conclusions, complete the
methodology's concurrent booking, retry/failure and controlled workload tests.
