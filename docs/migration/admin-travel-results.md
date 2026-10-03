# Admin Travel migration checkpoint

Admin Travel is the thirty-fourth live Spring Modulith business module. It is an administration facade over the published Travel and Travel2 APIs. The module graph verifies those two dependencies. Its former `ts-admin-travel-service:16114` address is behind an independent legacy/module switch.

The deployed JAR was the contract baseline. It combines both journey lists, chooses Travel for `G`/`D` train types and trip IDs, and chooses Travel2 otherwise. Unlike the checked-in source, the deployed facade does not validate stations, train types or routes before forwarding writes. The module follows the deployed behavior.

An isolated candidate matched the legacy list and role rules. It created, updated and deleted one G trip and one Z trip against copies of the Travel and Travel2 Mongo databases. It also matched the legacy invalid-delete response. Maven tests, the 34-module checkpoint and an Admin Travel-only rollback rehearsal passed. A port 8080 request returned HTTP 200, 10 trips and `X-AdminTravel-Backend: module`. The candidate container was removed after testing; the isolated database copies remain under `ts-admin-travel-candidate`.

The admin page had stale field names from an older API contract. Its displayed trip fields, train/station selectors and create/update payload now use the deployed `trainTypeId`, station IDs and `startingTime`/`endTime` fields. The UI was rebuilt from the deployed dashboard image with the existing order-list fix retained. For a browser check, sign in as administrator and open **Admin Panel → Travel** (`http://localhost:8080/admin_travel.html`). Inspect `GET /api/v1/admintravelservice/admintravel` in DevTools for `X-AdminTravel-Backend: module` and a populated list. The isolated candidate exercised writes; the live cutover verification was read-only.

Run `python docs/migration/verify_checkpoint.py` for the full stack or `python docs/migration/verify_admin_travel_rollback.py` for this route's rollback rehearsal. Next in the planned sequence: Admin Order.
