# Seat migration checkpoint

Historical fifth-module checkpoint from 30 September 2026. The newer
[Security checkpoint](security-results.md) supersedes the running-state details below.
Seat was the fifth Spring Modulith module in the shared
Spring Boot 3.5.16 / Java 21 host. Station, Orders, OrderOther and Config remain
on the same host. The other business services remain separate microservices.

## Implementation

- The `trainticket.seat` module preserves the deployed Seat service's welcome,
  allocation and left-ticket routes under `/api/v1/seatservice`. Its public API
  is separate from the internal controller, allocation rules and Travel adapter.
- Seat calls the public Orders, OrderOther and Config module APIs in-process.
  Travel and Travel2 are still microservices, so Seat calls their route and train
  type endpoints over HTTP. Spring Modulith verifies those three local module
  dependencies.
- Seat owns no database and does not write an order. The compatibility proxy
  holds the former `ts-seat-service:18898` address used by Preserve, PreserveOther,
  Rebook and the search services. Its response header is `X-Seat-Backend: module`.
  The UI gateway does not expose Seat's endpoint directly on port 8080.
- The deployed Seat service can loop indefinitely if every seat number is sold.
  The module returns a failed `No seat available` response in that case. Other
  observed request and response contracts remain compatible.

## Validation

- The Maven build passed **22 tests**, including Spring Modulith's five-module
  `ApplicationModules.verify()` and Seat boundary checks.
- A separate read-only five-module candidate passed **17 checks** against the
  deployed Seat service. These covered G and Z trains, both seat classes, full
  and partial journeys, and random allocation response constraints. Seat
  numbers are random, so the comparison validates their bounds and response
  semantics rather than requiring equal numbers.
- Both real booking workflows passed after Seat cutover: Preserve/Orders and
  PreserveOther/OrderOther each completed search, booking, wallet payment,
  cancellation and refund. Their cancelled synthetic orders remain in the
  ignored fixture for checkpoint verification.
- The live checkpoint passed before and after Seat's router switch. A Seat-only
  rollback rehearsal returned the router to legacy, matched availability,
  passed the checkpoint, then restored module routing and passed it again.

The running image is `train-ticket/ts-modulith:seat-candidate`
(`sha256:24937574343ba2b611255fceb73b05660a1b795f6f7a933e978da7b6`).
Routing state is in ignored `deployment/migration/.state/`; preserve it and
the original MongoDB volumes.

## Continue

Run `python docs/migration/run_hybrid.py` and
`python docs/migration/verify_checkpoint.py`. For side-by-side checks, run
`python docs/migration/run_hybrid.py --comparisons` and
`python docs/migration/verify_seat_candidate.py`. See [the testing guide](TESTING.md)
for other module checks and individual rollback commands.

Security is next in the [migration sequence](migration-plan.md). Seat allocation
still samples an available seat and relies on a later order write; it does not
reserve a seat atomically. Concurrent booking, retries and failure recovery
need a separate controlled test before claiming stronger booking guarantees.
