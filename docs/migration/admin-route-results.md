# Admin Route migration checkpoint

Admin Route is the thirty-third live Spring Modulith business module. It is a stateless facade over the published Route API, and Spring Modulith verifies that single dependency. Its old `ts-admin-route-service:16113` address is now behind an independent legacy/module switch.

The deployed JAR was the behavior baseline. Unlike the checked-in service source, it forwards route writes directly to Route without checking Station. The port follows the deployed behavior. An isolated candidate matched the legacy catalogue, welcome and role rules, and the invalid-distance response. It also created, modified and deleted a route in a copied Route Mongo database. Live Route data was unchanged by candidate testing.

Maven tests, the 33-module hybrid checkpoint and an Admin Route-only rollback rehearsal passed. A gateway request returned HTTP 200, 10 routes and `X-AdminRoute-Backend: module`. The candidate container was removed after testing; its database copy remains under `ts-admin-route-candidate` in the Route Mongo container.

For a browser check, sign in as administrator and open **Admin Panel → Routes** (`http://localhost:8080/admin_route.html`). In DevTools Network, inspect `GET /api/v1/adminrouteservice/adminroute` for `X-AdminRoute-Backend: module`. The isolated candidate exercised create, update and delete; the live cutover verification was read-only.

Run `python docs/migration/verify_checkpoint.py` for the full stack or `python docs/migration/verify_admin_route_rollback.py` for this route's rollback rehearsal. Next in the planned sequence: Admin Travel.
