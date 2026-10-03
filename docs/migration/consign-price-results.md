# ConsignPrice migration checkpoint

ConsignPrice is the twenty-fourth live Spring Modulith business module. Its existing service address at port 16110 routes through a compatibility proxy to the shared host and returns `X-ConsignPrice-Backend: module`. The Consign microservice remains separate and continues to call that address. The module has no dependencies on other business modules and retains its own Mongo `consign_price` collection and independent write gate.

The deployed JAR uses MongoDB, unlike the checked-out entity's JPA annotations. Its startup seeder has left four records with index 0 in the live collection. The module does not seed again and reads the same first record as the deployed service. The live collection was backed up to ignored `deployment/migration/.state/backups/consign-price.archive` before cutover.

An isolated candidate passed 26 comparisons: authentication, configuration, description, quotes across weights and regions, and a configuration update against separate test databases. Maven tests passed, including Spring Modulith boundary verification. The live checkpoint passed across all 24 modules. An independent rollback rehearsal switched only ConsignPrice to legacy and back, compared price/configuration on both sides, and verified that the inactive module returned 503 for a write.

An integration check submitted a disposable consignment through port 8080 to the still-running Consign microservice. Consign called the routed ConsignPrice module and returned the module's 16.0 quote for a 3 kg beyond-region shipment. The synthetic shipment was then removed.

To check the route directly, request `http://localhost:16110/api/v1/consignpriceservice/consignprice/3/false` with a logged-in token and look for HTTP 200, `data: 16.0` and `X-ConsignPrice-Backend: module`. The browser gateway does not expose this pricing endpoint directly. In the UI, open **Order List → Consign** on an eligible order; submission uses the separate Consign service and the module behind it. Automated checks: `python docs/migration/verify_checkpoint.py`, `python docs/migration/verify_consign_price_rollback.py`, and `python docs/migration/verify_consign_price_integration.py`.

Consign has since been migrated; see the [Consign checkpoint](consign-results.md). WaitOrder remains pending because its service and database are absent from the running stack.
