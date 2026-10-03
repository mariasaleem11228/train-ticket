# Execute migration checkpoint ? 1 October 2026

Execute is the eighteenth business module in the shared Spring Modulith host. The original `ts-execute-service:12386` identity and `/api/v1/executeservice/**` API now route through an independently switchable compatibility proxy. The live route is in `module` mode and adds `X-Execute-Backend: module`; the original container and a legacy rollback instance are retained.

The module calls published Orders and OrderOther APIs instead of HTTP. Both Execute GET operations mutate order status, so the module checks `EXECUTE_WRITES_ENABLED` and the `execute` ownership entry before reading or changing an order. The host retains the deployed success and error messages, including their differences between Orders and OrderOther. Execute still requires the legacy USER or ADMIN JWT roles.

## Evidence

- The isolated candidate passed 22 checks against the deployed Execute service. These covered the welcome route, both order types, collect ? execute transitions, repeated execute failure, and resulting order states. Its test orders used separate Orders and OrderOther Mongo databases.
- Before the host upgrade, the live `orders` collections were backed up under ignored `.state/backups/execute-orders.archive` and `execute-order-other.archive`.
- The shared host reported 18 modules with Execute depending only on Orders and OrderOther. `verify_checkpoint.py` passed after cutover.
- The rollback rehearsal switched only Execute to legacy, confirmed direct module writes returned HTTP 503, completed collect ? execute on both order types, returned to module mode, and repeated both transitions. Evidence is in `ts-modulith/target/evidence/execute-rollback.json`.
- Through browser-facing port 8080, a synthetic paid order returned HTTP 200 and `X-Execute-Backend: module` for both `/execute/collected/{id}` and `/execute/execute/{id}`.

Synthetic orders from these checks remain in the order databases as audit data. They used generated account IDs and train numbers; no wallet payment was performed for the status-transition checks. The isolated candidate was kept separate from live order data.

## Resume and inspect

```powershell
python docs/migration/run_hybrid.py
python docs/migration/verify_checkpoint.py
python docs/migration/verify_execute_rollback.py
```

After a Docker restart, `run_hybrid.py` invokes `recover_proxy_ips.py` to reclaim fixed proxy addresses before starting dynamic-IP containers. It was needed during this checkpoint after Docker Desktop stopped unexpectedly.

For a UI check, book and pay a ticket, then use **Execute Flow ? Ticket Collect** followed by **Enter Station**. In DevTools, inspect the responses to `GET /api/v1/executeservice/execute/collected/{orderId}` and `GET /api/v1/executeservice/execute/execute/{orderId}`. Each should have `X-Execute-Backend: module`. An order that is unpaid, cancelled or already used correctly returns `Order Status Wrong`.

WaitOrder remains pending: it is not part of the running Compose deployment and its configured MySQL database is unavailable. This stage moved Execute ahead so the side-by-side and rollback checks could use the actual running service.
