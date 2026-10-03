# Security migration checkpoint

30 September 2026. Security is the sixth Spring Modulith business module in the
shared Spring Boot 3.5.16 / Java 21 host. Station, Orders, OrderOther, Config
and Seat remain on that host. Other services continue as microservices.

## Implementation

- `trainticket.security` owns the order-limit policy API and the original
  `ts.security_config` MongoDB collection. The host's JWT filter and HTTP
  authentication configuration moved to `trainticket.auth`, so Spring Modulith
  can identify Security as a distinct business module.
- Security reads order counts through the public Orders and OrderOther Java
  APIs. It preserves the deployed service's policy routes, messages, UUID
  subtype 3 encoding and `_class` marker. It does not re-run the legacy
  startup seeder; the two existing policies stay in MongoDB.
- The old `ts-security-service:11188` address is held by a compatibility proxy.
  It reports `X-Security-Backend: module`. Security has its own write-ownership
  gate and can be rolled back without stopping the other five modules.

## Validation

- Maven passed **24 tests**, including Spring Modulith's six-module
  `ApplicationModules.verify()` and Security boundary checks.
- The read-only live candidate and isolated legacy/module copies passed
  **15 comparison checks**: policy reads, booking-limit decisions, create,
  duplicate, update, delete, legacy UUIDs and rejection of candidate writes.
- A live MongoDB archive of the two original policy documents is retained at
  ignored `ts-modulith/target/evidence/security-backup.archive`.
- Both Preserve booking flows passed with Security routed to the module,
  including search, booking, wallet payment, cancellation and refund.
- The Security-only rollback rehearsal passed: legacy read and updated a
  module-created policy, the inactive module rejected writes, and the module
  read the legacy update after switching back. The disposable policy was
  removed. The full checkpoint passed in both router modes.

The running image is `train-ticket/ts-modulith:security-candidate`
(`sha256:980af19f56dd72bd475a5ce62851067d909db3072f2711864e809bb603c6d86e`).
Preserve ignored `deployment/migration/.state/`, the MongoDB volumes and the
backup archive for recovery.

## Continue

Run `python docs/migration/run_hybrid.py`, then
`python docs/migration/verify_checkpoint.py`. For side-by-side tests, run
`python docs/migration/run_hybrid.py --comparisons` followed by
`python docs/migration/verify_security.py`. See [the testing guide](TESTING.md).

Train is next in the [migration plan](migration-plan.md). A controlled
concurrent-booking and failure-recovery test remains necessary before drawing
stronger conclusions about booking correctness.
