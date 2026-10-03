# Basic migration checkpoint

30 September 2026. Basic is the tenth Spring Modulith business module in the
shared host. Its compatibility proxy retains `ts-basic-service:15680` for
unmigrated callers. `X-Basic-Backend: module` identifies the current backend.

## Deployed contract

The running `codewisdom/ts-basic-service:0.2.0` differs from checkout source.
The deployed API has `/welcome`, `GET /basic/{stationName}`, and
`POST /basic/travel`. The checkout's batch `/basic/travels` endpoint is absent
in the deployed image. Basic owns no database. It composes Station, Train,
Route and Price. The new module calls those four published Java APIs directly;
the existing microservices continue to use Basic's HTTP identity.

## Evidence

- Maven package, Spring Modulith verification and ArchUnit boundaries passed.
- `verify_basic.py` passed 26 side-by-side checks against the live catalogues:
  station lookup, all ten configured travel fares, missing data and route order.
- `verify_basic_rollback.py` switched Basic alone to the original legacy image,
  checked its response, and returned Basic to module routing.
- Both booking variants completed journey search, booking, wallet payment,
  cancellation and refund with Basic on the module route.
- `verify_checkpoint.py` passed with ten business modules, all compatibility
  routes and retained synthetic orders.

The deployed Basic service returns HTTP 500 when its Train lookup returns 404
for an unknown train. The module preserves that status, although Spring Boot
versions produce different error JSON. No data copy or write handover was
needed for Basic because it is read-only.

## Repeat checks

```powershell
python docs/migration/run_hybrid.py
python docs/migration/verify_checkpoint.py
(Invoke-WebRequest http://localhost:15680/api/v1/basicservice/welcome -UseBasicParsing).Headers['X-Basic-Backend']
Invoke-RestMethod http://localhost:18080/actuator/modulith | ConvertTo-Json -Depth 8
```

The header should be `module`. To rehearse independent rollback, run
`python docs/migration/verify_basic_rollback.py`; it returns Basic to module
mode. To compare the candidate while the original Basic container is still
active, use `python docs/migration/run_hybrid.py --basic-comparison` and then
`python docs/migration/verify_basic.py`.

Next planned service: Travel. Full application migration remains incomplete.
