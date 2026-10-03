# Train migration checkpoint

30 September 2026. Train is the seventh Spring Modulith business module in the
shared host. The compatibility proxy retains `ts-train-service:14567`; its
`X-Train-Backend: module` header proves which implementation served a request.
Other services remain separate microservices.

## Deployed contract and data

The deployed `codewisdom/ts-train-service:0.2.0` image differs from the checkout:
it uses MongoDB collection `ts.trainType`, with string `_id` and fields
`economyClass`, `confortClass`, and `averageSpeed`. The host reads the original
database and preserves its `_class` value on writes. It does not run the legacy
startup seeder. Six catalogue records were archived before cutover at
`deployment/migration/.state/backups/train.archive` (ignored; preserve this file).

`TrainOperations` is the module's exported Java API for later Travel and admin
ports. Train currently has no Java dependency on another business module.
Existing callers continue to use the old HTTP identity through the proxy.

## Checks performed

- Maven package and Spring Modulith structure/architecture tests passed.
- `verify_train.py`: 22 checks passed. A read-only candidate matched live data;
  isolated copies matched for all six records, missing IDs, welcome, create,
  duplicate create, update, delete, and the candidate write gate.
- `verify_train_rollback.py`: a module-created record was read and updated by
  the legacy backend, the module rejected writes during rollback, and the module
  read the updated record after switching back. The disposable record was removed.
- Both `verify_booking.py train-module` and `verify_booking_other.py train-module`
  passed search, booking, wallet payment, cancellation, and refund. Proxy logs
  show legacy Java callers requesting Train records through the compatibility
  route during these flows.
- `verify_checkpoint.py` passed with seven Spring Modulith modules and all
  retained synthetic orders readable.

During verification, the checkpoint script sent a POST to Train because Train
was omitted from its GET-only route list. That created one null-ID record. The
script was fixed, the record was identified against the pre-cutover archive and
removed, and the checkpoint passed again. This also shows the deployed contract
accepts an object without `id`; application callers should supply one.

## Resume and inspect

```powershell
python docs/migration/run_hybrid.py
python docs/migration/verify_checkpoint.py
Invoke-WebRequest http://localhost:14567/api/v1/trainservice/trains -UseBasicParsing |
  Select-Object -ExpandProperty Headers
Invoke-RestMethod http://localhost:18080/actuator/modulith | ConvertTo-Json -Depth 8
```

The Train API is directly exposed on port 14567. The UI gateway on port 8080
is not required for this check. To rehearse rollback again, run
`python docs/migration/verify_train_rollback.py`; it creates and removes a
disposable record and returns Train to module mode.

The earlier `ts-modulith/target/evidence` files were cleared by the Maven clean
build for this stage. The live routing/data state and the ignored Train archive
remain intact. Regenerate prior comparison files with their verification scripts
if old stage install gates are needed later. Avoid `mvn clean` when preserving
ephemeral evidence; `mvn package` is enough for subsequent builds.

Next planned service: Route. The full application is not yet a modular monolith.
