# Travel2 migration checkpoint

30 September 2026. Travel2 is the twelfth Spring Modulith business module.
The compatibility proxy retains the original `ts-travel2-service:16346` identity;
`X-Travel2-Backend: module` identifies the live backend. Route Plan is next.

## Deployed contract and data

The running `codewisdom/ts-travel2-service:0.2.0` uses MongoDB `ts.trip` and
composite trip IDs. This differs from the checkout's JPA implementation. Its
five live records were backed up to
`deployment/migration/.state/backups/travel2.archive` before cutover. The module
keeps the deployed Mongo shape and uses published Train, Route, Orders and Seat
APIs; TicketInfo remains an HTTP dependency. The rollback image removes only
the startup sample-trip seeder so deletions remain deleted during rollback.

The deployed Travel2 API accepts unauthenticated trip updates. The module
preserves that behavior for compatibility; its write-ownership gate still
rejects all writes when Travel2 is routed to legacy. Review that legacy access
rule before any deployment beyond this benchmark environment.

## Verification

- Maven module and architecture tests passed. A candidate host with both
  Travel and Travel2 enabled served both APIs and reported twelve modules.
- `verify_travel2.py` passed 42 side-by-side checks covering all five trips,
  search and fares, trip detail, missing inputs, admin reads, access behavior,
  isolated create/update/delete, and preservation of live data.
- `verify_travel2_rollback.py` switched only Travel2 to legacy, verified a
  module-created trip and a legacy update, checked the module write gate,
  returned to the module and removed the disposable trip. The five original
  records remained unchanged.
- Both booking variants completed search, booking, wallet payment,
  cancellation and refund. `verify_checkpoint.py` passed the twelve-module
  graph, original service routes and retained synthetic orders.

## Resume and repeat

```powershell
python docs/migration/run_hybrid.py
python docs/migration/verify_checkpoint.py
(Invoke-WebRequest http://localhost:16346/api/v1/travel2service/trips -UseBasicParsing).Headers['X-Travel2-Backend']
```

The header should be `module`. Use
`python docs/migration/verify_travel2_rollback.py` to repeat the rollback
rehearsal. For isolated comparisons, run
`python docs/migration/run_hybrid.py --travel2-comparison` followed by
`python docs/migration/verify_travel2.py`.
