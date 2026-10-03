# Price migration checkpoint

30 September 2026. Price is the ninth Spring Modulith business module in the
shared host. Its compatibility proxy retains `ts-price-service:16579` for
unmigrated callers. `X-Price-Backend: module` identifies the current backend.

## Deployed contract and storage

The running `codewisdom/ts-price-service:0.2.0` differs from checkout source.
It uses MongoDB collection `ts.price_config`, with Java-legacy UUID binary
subtype 3 IDs. The module retains that representation, the existing response
messages, and HTTP 201 on create. The deployed controller accepts a request
body for `DELETE /api/v1/priceservice/prices` and does not expose the checkout's
batch lookup endpoint. Price has no Java dependency on another business module;
Travel and other unmigrated callers still use the old HTTP identity.

The original image writes sample prices on startup. The retained rollback
image is byte-identical except for removal of `price.init.InitData.class`,
so it cannot overwrite later price edits when started. Ten live records were
backed up before cutover at `deployment/migration/.state/backups/price.archive`
(ignored; preserve it). The module does not seed on startup.

## Evidence

- Maven package and Spring Modulith/ArchUnit boundaries passed.
- `verify_price.py`: 26 side-by-side checks passed. The read-only candidate
  matched all 10 live records. Isolated database copies matched for lookups,
  create, update, delete, missing values, and the module write gate.
- `verify_price_rollback.py`: a module-created price was read and updated by
  the legacy backend, the module rejected writes during rollback, and the
  module read the update after switching back. The disposable price was removed.
- Both booking variants passed search, booking, wallet payment, cancellation,
  and refund with Price on the module route.
- `verify_checkpoint.py` passed with nine Spring Modulith modules and retained
  synthetic orders readable. The live Price collection still contains 10 records.

Docker Desktop became unresponsive during the first comparison restore and was
restarted. The existing eight-module checkpoint passed after recovery before
the Price cutover. The resume script now starts fixed-IP proxies before dynamic
containers and relocates a dynamic occupant if a Docker restart reused a proxy
address. The comparison was rerun on copied data and passed before switching.

## Repeat checks

```powershell
python docs/migration/run_hybrid.py
python docs/migration/verify_checkpoint.py
Invoke-WebRequest http://localhost:16579/api/v1/priceservice/prices -UseBasicParsing |
  Select-Object -ExpandProperty Headers
Invoke-RestMethod http://localhost:18080/actuator/modulith | ConvertTo-Json -Depth 8
```

For isolated Price comparison endpoints only, run
`python docs/migration/run_hybrid.py --price-comparison`, then
`python docs/migration/verify_price.py`. This avoids starting every older test
host at once. To rehearse rollback, run
`python docs/migration/verify_price_rollback.py`; it returns Price to module mode.

Next planned service: Basic. Full application migration remains incomplete.
