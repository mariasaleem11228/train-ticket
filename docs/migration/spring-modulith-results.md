# Spring Modulith upgrade checkpoint

Historical three-module checkpoint from 30 September 2026. The newer
[Config checkpoint](config-results.md) supersedes the running-state details below.
At this checkpoint, the hybrid used Spring Modulith 1.4.13 on
Spring Boot 3.5.16 and Java 21. Station, Orders and OrderOther remain the only
ported business services. Other services still run as separate microservices;
the entire application has not yet been consolidated.

## Implemented

- The `ts-modulith` host declares its three business packages with
  `@ApplicationModule` and marks the bootstrap with `@Modulithic`.
- Spring Modulith's verification test checks the package boundaries and module
  dependencies. Orders and OrderOther use Station's public Java interface and
  have `allowedDependencies = "station"`. Security and runtime support remain
  shared infrastructure outside the three declared business modules.
- The host exposes `/actuator/modulith` on its local port 18080. Its live model
  reports exactly `station`, `orders`, and `orderother`; the latter two depend on
  `station`. The checkpoint script checks this model along with the UI routes,
  health and retained orders.
- The old service addresses remain behind independent compatibility routers.
  Each module has a separate write-ownership gate and a legacy fallback. The
  Spring Modulith image is `train-ticket/ts-modulith:spring-modulith-1.4`.
- Servlet and validation imports use Jakarta packages, and the security setup
  uses Spring Security 6. The legacy HTTP payloads, JWT adapter and Mongo
  collections remain compatible with the tested flows.

## Verification performed

- Spring Modulith `ApplicationModules.verify()`, the Station
  `@ApplicationModuleTest`, existing architecture tests and HTTP contract tests
  pass under the upgraded host.
- Isolated legacy-versus-module comparisons passed: Station 32/32, Orders
  33/33, OrderOther 31/31. The known intentional differences are rejection of
  malformed JWTs and stricter OrderOther authorisation.
- Both normal and OrderOther booking workflows passed against the upgraded
  live hybrid, including search, booking, wallet payment, cancellation and
  refund. Cancelled synthetic orders remain available for checkpoint checks.
- A read-only candidate comparison passed 15/15 checks before cutover. A
  rollback rehearsal confirmed that the previous host image can read orders
  created by the upgraded host, then restored the Spring Modulith image.

## Continue from this checkpoint

From the repository root, use `python docs/migration/run_hybrid.py` followed by
`python docs/migration/verify_checkpoint.py`. Inspect the module graph with
`Invoke-RestMethod http://localhost:18080/actuator/modulith | ConvertTo-Json -Depth 8`.
Run `mvn -f ts-modulith/pom.xml test` for boundary and context tests. For
side-by-side comparisons, run `python docs/migration/run_hybrid.py --comparisons`
and the three `verify_station.py`, `verify_orders.py`, and
`verify_order_other.py` scripts in this directory. See [the testing guide](TESTING.md)
for endpoints and rollback steps.

Next service: Config, followed by Seat and Security under the
[migration plan](migration-plan.md). Apply the same one-service sequence:
characterise the legacy contract, add a declared module and public API, run
isolated comparisons, exercise real workflows, then cut its router over with
its own write gate and rollback path. This framework upgrade establishes the
module model; it does not port the remaining services by itself.
