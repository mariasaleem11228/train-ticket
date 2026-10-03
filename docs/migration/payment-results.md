# Payment migration checkpoint

Payment is the nineteenth Spring Modulith business module. The deployed Payment image uses MongoDB even though its checked-in source configuration refers to MySQL. The module keeps the deployed REST contract and the existing `ts.payment` and `ts.addMoney` collections. It has no module dependencies. The compatibility proxy keeps `ts-payment-service:19001` available to other services, and `X-Payment-Backend` identifies its active target.

The candidate used `payment_module_migration_test`, seeded with a copy of the 12 existing payment records. Its 15 comparison checks covered the module graph, welcome route, existing query result, duplicate payment response, new payment and retention, and add-money response. The comparison exposed an older-record detail: the deployed service returns `""` for a missing `userId`; the module now does the same. Synthetic tests use unique `MIGPAY-` order IDs and `migration-test-` user IDs. No real user wallet was credited.

Before cutover, both live collections were backed up under ignored `deployment/migration/.state/backups/`. The host was upgraded behind maintenance routes, then Payment was switched from legacy to module mode. The rollback rehearsal passed: the legacy service could read and write through the proxy, inactive module writes returned 503, and both implementations read the synthetic payment written by the other. The full checkpoint passed for all nineteen module routes and retained booking fixtures. `mvn -q -f ts-modulith/pom.xml test` passed.

From the still-running Inside Payment container, `ts-payment-service` resolves to the Payment compatibility proxy's IP, confirming the service-to-service seam remains in place. The checkpoint also confirms unauthenticated Payment reads return 403 and a USER role can read.

Verify the active implementation with an authenticated request to `http://localhost:19001/api/v1/paymentservice/welcome` or `/payment`; the response header must be `X-Payment-Backend: module`. The current UI NGINX config does not expose a matching `/api/v1/paymentservice/**` route on port 8080, so use port 19001 for this service. There is no dedicated Payment screen in the UI. The UI payment path goes through Inside Payment, which remains a separate microservice.

To rehearse an independent rollback, run `python docs/migration/verify_payment_rollback.py`. To switch manually, run `python docs/migration/hybrid_routing.py legacy payment` and return with `python docs/migration/hybrid_routing.py module payment`. `python docs/migration/verify_checkpoint.py` checks the route and module graph afterward.

Next: Inside Payment. WaitOrder remains pending until its service and configured MySQL database are available in this deployment. A complete end-to-end wallet and refund test belongs to the Inside Payment and Cancel stages; this checkpoint establishes the Payment service's deployed contract and write handover.
