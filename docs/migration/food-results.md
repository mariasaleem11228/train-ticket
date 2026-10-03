# Food migration checkpoint

Food is the twenty-seventh live Spring Modulith business module. It owns the existing Mongo `foodorder` collection (20 orders at backup) and exposes the original `/api/v1/foodservice` API. Menu lookup calls the published Food Map, Travel, Station and Route module APIs. Creating a food order saves it in Mongo and publishes a delivery message to RabbitMQ's `food_delivery` queue.

The 20 food orders were backed up before cutover. The isolated candidate passed 24 comparisons against the deployed service: existing order reads, menu success and failure cases, duplicate handling, create/update/delete, and one delivery message to the candidate queue. The live `food_delivery` queue count did not change during candidate testing. Maven tests and the Spring Modulith boundary check passed.

The shared host now contains 27 modules. The full checkpoint passed after Food was routed to the module. A Food-only rollback rehearsal returned the route to the legacy service, confirmed the same menu and the inactive module's write refusal, then returned the route to the module. The checkpoint passed again afterward. The rehearsal used read-only live requests, so it did not add a delivery message to the live queue.

To test in the UI: open **Ticket Reserve**, search a trip, choose **Booking**, then select **Need Food** on the booking page. The browser calls `/api/v1/foodservice/foods/{date}/{start}/{end}/{tripId}`. In DevTools, check that the response has `X-Food-Backend: module`. A direct check is `http://localhost:18856/api/v1/foodservice/foods/2026-10-03/Shang%20Hai/Su%20Zhou/D1345`; the menu should contain four train foods and stores at two stations. The gateway at port 8080 should return the same response and header.

Run `python docs/migration/verify_checkpoint.py` for the complete live hybrid, or `python docs/migration/verify_food_rollback.py` to repeat the Food-only rollback rehearsal. The latter briefly switches Food to the legacy service before restoring it.

The live create-to-delivery-consumer flow has not been exercised by this checkpoint. The module's publish behavior was verified with an isolated RabbitMQ queue; the running stack currently has messages in `food_delivery` and no active consumer.
