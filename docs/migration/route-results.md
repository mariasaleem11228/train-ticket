# Route migration checkpoint

30 September 2026. Route is the eighth Spring Modulith business module in the
shared host. The compatibility proxy retains `ts-route-service:11178`, so
unmigrated callers still use their original HTTP target. `X-Route-Backend: module`
shows the current owner. The remaining business services run separately.

## Deployed contract and storage

The deployed `codewisdom/ts-route-service:0.2.0` differs from checkout source.
It stores records in MongoDB collection `ts.routes`, with `stations`, `distances`,
`startStationId`, and `terminalStationId`. The deployed controller has no
`/routes/byIds` endpoint. The module preserves its public paths, result messages,
route order, station-pair filtering, and create/modify semantics.

The original image writes all sample routes on startup. The retained rollback
image is byte-identical except that `route.init.InitData.class` is removed; it
cannot overwrite route edits when started for rollback. The module also does not
seed. Ten live records were backed up before cutover at
`deployment/migration/.state/backups/route.archive` (ignored; preserve it).

The deployed Route security configuration allows anonymous writes in practice:
its broad allow rule matches before its later admin rules. The module preserves
that behavior for compatibility. Tightening authorization needs a separate
client and policy change.

## Evidence

- Maven package and Spring Modulith/ArchUnit boundaries passed.
- `verify_route.py`: 30 checks passed against isolated legacy/module database
  copies and a read-only candidate on live data. Covered all 10 routes, station
  pairs, missing IDs, create, modify, delete, validation, anonymous access,
  module write gate, and unchanged live data.
- `verify_route_rollback.py`: a module-created route was read and modified by
  the legacy backend, the module rejected writes during rollback, and the module
  read the modified route after switching back. The disposable route was removed.
- Both booking variants passed search, booking, wallet payment, cancellation,
  and refund with Route on the module route.
- `verify_checkpoint.py` passed with eight Spring Modulith modules and retained
  synthetic orders readable.

## Repeat checks

```powershell
python docs/migration/run_hybrid.py
python docs/migration/verify_checkpoint.py
Invoke-WebRequest http://localhost:11178/api/v1/routeservice/routes -UseBasicParsing |
  Select-Object -ExpandProperty Headers
Invoke-RestMethod http://localhost:18080/actuator/modulith | ConvertTo-Json -Depth 8
```

The Route API is directly available on port 11178. To rehearse rollback again,
run `python docs/migration/verify_route_rollback.py`; it returns routing to the
module. Keep `.state`, the Route archive, and the no-seed rollback image.

Next planned service: Price. Full application migration remains incomplete.
