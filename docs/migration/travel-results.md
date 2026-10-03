# Travel migration checkpoint

30 September 2026. Travel is the eleventh business module in the Spring
Modulith host. Its original `ts-travel-service:12346` identity remains available
through a compatibility proxy. `X-Travel-Backend: module` identifies the live
backend. Travel2 is the next service in the planned sequence.

## Deployed contract and implementation

The running `codewisdom/ts-travel-service:0.2.0` differs from checkout source.
The deployed API covers trip reads and admin writes, route and train type
lookups, journey search, trip detail and the admin trip catalogue. The checkout's
`/trips/left_parallel` endpoint is absent. Travel owns the MongoDB `ts.trip`
collection, including composite trip IDs and the original `_class` value.

The module uses local published APIs from Train, Route, Orders and Seat. TicketInfo
remains a microservice reached over HTTP. The original Travel startup seeder
would recreate deleted sample trips during rollback, so the rollback image
removes that seeder. The five-record live collection was backed up at
`deployment/migration/.state/backups/travel.archive` before cutover.

## Verification

- Maven tests passed, including Spring Modulith module verification and
  architecture boundaries.
- `verify_travel.py` passed 42 side-by-side checks on live reads and isolated
  copies for writes. It covered all five trips, search and fares, detail,
  route/train lookups, missing inputs, admin authorization and CRUD.
- `verify_travel_rollback.py` created a disposable trip in the module,
  switched only Travel to legacy, updated it there, confirmed the module's
  write gate, returned to the module and removed it. The original five trips
  remained unchanged.
- Both booking variants passed search, booking, wallet payment, cancellation
  and refund after Travel cutover. `verify_checkpoint.py` passed all eleven
  routes and the Spring Modulith dependency model.

## Resume and repeat

```powershell
python docs/migration/run_hybrid.py
python docs/migration/verify_checkpoint.py
(Invoke-WebRequest http://localhost:12346/api/v1/travelservice/trips -UseBasicParsing).Headers['X-Travel-Backend']
```

The header should be `module`. To repeat the independent rollback rehearsal,
run `python docs/migration/verify_travel_rollback.py`. For isolated comparisons,
run `python docs/migration/run_hybrid.py --travel-comparison`, then
`python docs/migration/verify_travel.py`.

The whole application has not yet been migrated; the remaining services stay
available as microservices during subsequent cutovers.
