# Test the current hybrid application

Checkpoint: 4 October 2026. All 44 identified business services now have Spring
Modulith modules in one Spring Boot 3.5.16/Java 21 host. TicketInfo's contract
matches the retained legacy service. WaitOrder's HTTP and persistence paths
work; automatic booking retries are enabled with a durable lease and a stable
order ID for replay. A separate internal Trip Catalog module makes 45 runtime
modules; Seat, Travel and Travel2 use its published API. Avatar uses a colocated
Python dlib utility.
See the [WaitOrder migration results](wait-order-results.md).

## Resume the hybrid

Start Docker Desktop, then open PowerShell in `C:\TrainTicketMSsProject\train-ticket`:

```powershell
python docs/migration/run_hybrid.py
python docs/migration/verify_checkpoint.py
Invoke-RestMethod http://localhost:18080/actuator/modulith | ConvertTo-Json -Depth 8
```

The launcher resumes this existing deployment and preserves its data and routing.
It is not a fresh-machine installer. Allow the existing services time to start
after a Docker restart. The checkpoint verifies the UI and direct service routes,
host health, authentication on protected endpoints, retained synthetic orders,
and the 45-module Spring Modulith runtime graph. Rebook depends on Orders,
OrderOther, Station, Travel, Travel2, Seat and Inside Payment through their
published APIs. The Actuator endpoint is on the host's
local port 18080; the browser-facing port 8080 does not expose it.

- Application: http://localhost:8080
- Shared host health: http://localhost:18080/actuator/health
- Spring Modulith model: http://localhost:18080/actuator/modulith
- Seat service: http://localhost:18898/api/v1/seatservice/welcome
- Security policies: http://localhost:11188/api/v1/securityservice/securityConfigs (requires a test login)
- Train catalogue: http://localhost:14567/api/v1/trainservice/trains (`X-Train-Backend: module`)
- Route catalogue: http://localhost:11178/api/v1/routeservice/routes (`X-Route-Backend: module`)
- Price catalogue: http://localhost:16579/api/v1/priceservice/prices (`X-Price-Backend: module`)
- Basic welcome: http://localhost:15680/api/v1/basicservice/welcome (`X-Basic-Backend: module`)
- Travel trips: http://localhost:12346/api/v1/travelservice/trips (`X-Travel-Backend: module`)
- Travel2 trips: http://localhost:16346/api/v1/travel2service/trips (`X-Travel2-Backend: module`)
- Route Plan welcome: http://localhost:14578/api/v1/routeplanservice/welcome (`X-RoutePlan-Backend: module`)
- Travel Plan welcome: http://localhost:14322/api/v1/travelplanservice/welcome (`X-TravelPlan-Backend: module`)
- Contacts welcome: http://localhost:12347/api/v1/contactservice/contacts/welcome (`X-Contacts-Backend: module`)
- Preserve welcome: http://localhost:14568/api/v1/preserveservice/welcome (`X-Preserve-Backend: module`)
- PreserveOther welcome: http://localhost:14569/api/v1/preserveotherservice/welcome (`X-PreserveOther-Backend: module`)
- Execute welcome: http://localhost:12386/api/v1/executeservice/welcome (`X-Execute-Backend: module`; requires login)
- Payment welcome: http://localhost:19001/api/v1/paymentservice/welcome (`X-Payment-Backend: module`; requires login)
- Inside Payment welcome: http://localhost:18673/api/v1/inside_pay_service/welcome (`X-InsidePayment-Backend: module`; requires login)
- Cancel welcome: http://localhost:18885/api/v1/cancelservice/welcome (`X-Cancel-Backend: module`; requires login)
- Rebook welcome: http://localhost:18886/api/v1/rebookservice/welcome (`X-Rebook-Backend: module`; requires login)
- Assurance types: http://localhost:18888/api/v1/assuranceservice/assurances/types (`X-Assurance-Backend: module`; requires a USER login)
- ConsignPrice quote: http://localhost:16110/api/v1/consignpriceservice/consignprice/3/false (`X-ConsignPrice-Backend: module`; requires login)
- Consign welcome: http://localhost:16111/api/v1/consignservice/welcome (`X-Consign-Backend: module`; requires login)
- Food Map train menu: http://localhost:18855/api/v1/foodmapservice/trainfoods/D1345 (`X-FoodMap-Backend: module`)
- Food menu: http://localhost:18856/api/v1/foodservice/foods/2026-10-03/Shang%20Hai/Su%20Zhou/D1345 (`X-Food-Backend: module`)
- Notification welcome: http://localhost:17853/api/v1/notifyservice/welcome (`X-Notification-Backend: module`)
- Login CAPTCHA: http://localhost:8080/api/v1/verifycode/generate (`X-VerifyCode-Backend: module`)
- Login: `POST http://localhost:8080/api/v1/users/login` (`X-Auth-Backend: module`)
- User profile: http://localhost:8080/api/v1/userservice/users/fdse_microservice (`X-User-Backend: module`)
- Admin Basic Info catalogues: http://localhost:8080/api/v1/adminbasicservice/adminbasic/stations (`X-AdminBasic-Backend: module`)
- Admin Route catalogue: http://localhost:8080/api/v1/adminrouteservice/adminroute (`X-AdminRoute-Backend: module`; requires an ADMIN login)
- Admin Travel list: http://localhost:8080/api/v1/admintravelservice/admintravel (`X-AdminTravel-Backend: module`; requires an ADMIN login)
- Admin Order list: http://localhost:8080/api/v1/adminorderservice/adminorder (`X-AdminOrder-Backend: module`; requires an ADMIN login). Open http://localhost:8080/admin.html after admin login.
- Admin User list: http://localhost:8080/api/v1/adminuserservice/users (`X-AdminUser-Backend: module`; requires an ADMIN login). Open http://localhost:8080/admin_user.html after admin login.
- Voucher: `POST http://localhost:8080/getVoucher` with `{"orderId":"<existing-order-id>","type":1}` for Orders or `type:0` for OrderOther (`X-Voucher-Backend: module`). The Order List screen calls this when you click Print Voucher on an eligible order.
- Avatar: open http://localhost:8080/upload_avatar.html and upload a clear face image. `POST /api/v1/avatar` should return the cropped image with `X-Avatar-Backend: module`.
- Delivery has no HTTP endpoint or standalone screen. A booking with food sends a `food_delivery` RabbitMQ message. Verify its persistence with `python docs/migration/verify_delivery_live.py`; see [Delivery migration results](delivery-results.md).
- Food Delivery has no current UI screen. Its API is on the shared host at http://localhost:18080/api/v1/fooddeliveryservice/welcome. Run `python docs/migration/verify_food_delivery_live.py` for catalogue pricing, CRUD and write-gate checks. The current port 8080 proxy has no Food Delivery route.
- TicketInfo: run `python docs/migration/verify_ticketinfo_live.py` to compare the local module with the retained legacy service on port 15681. Travel and booking modules call the local API.
- WaitOrder has no current UI screen or port-8080 route. Run `python docs/migration/verify_wait_order_live.py`; its authenticated API is at http://localhost:18080/api/v1/waitorderservice/welcome. The booking retry was tested in an isolated candidate; see [WaitOrder migration results](wait-order-results.md). Add `--write` only when you want a new synthetic wait-list entry; its deliberately invalid contact will retry until expiry.
- Local email inbox: http://localhost:8025

Run `mvn -f ts-modulith/pom.xml test` to check module boundaries and the Station
module's Spring context. The architecture test calls Spring Modulith's
`ApplicationModules.verify()`.

The shared-host image includes the Avatar Python worker. After packaging the
JAR, rebuild it with `docker build -f ts-modulith/Dockerfile.avatar -t
train-ticket/ts-modulith:trip-catalog-candidate ts-modulith`. The plain
`ts-modulith/Dockerfile` lacks that worker.

The Trip Catalog cutover was checked with
`python docs/migration/verify_trip_catalog_candidate.py` and
`python docs/migration/verify_trip_catalog_booking_candidate.py`. The first
compares Travel, Travel2 and Seat reads against the previous live host. The
second books both trip types into isolated Order databases. Both candidates
set the old Seat-to-Travel URLs to an unreachable address.

## Try the UI

1. Open the application and sign in with your local test account, or register one.
2. Search **Nan Jing** to **Shang Hai**, using a date about seven days ahead.
3. Select a journey, add/select a contact and book a second-class seat.
4. Open your orders. Payment requires a funded local wallet; cancel after payment
   to exercise the refund path. The benchmark may refund less than the full fare.
5. In browser developer tools, inspect both Order List `refresh` requests:
   Orders has `X-Orders-Backend: module`, and OrderOther has
   `X-OrderOther-Backend: module`. Station has `X-Station-Backend: module`.

To check the latest direct module calls, sign in through **Login**, open
**Ticket Reserve**, choose a future trip and select a contact. Choose
**Assurance** and **Need Food** before booking. For a consign check, also
select **Consign** and enter its details. The booking response is
`POST /api/v1/preserveservice/preserve` with `X-Preserve-Backend: module`;
the order should appear on **Order List**. Calls between modules run inside
the host and do not appear as separate browser Network requests. The isolated
candidate verified Auth, Preserve, Assurance, Food and Consign with their
legacy URLs disabled. An eligible test order's Cancel action also exercises
the Cancel module's local User lookup.

Config's route is `http://localhost:8080/api/v1/configservice/configs` and its
response has `X-Config-Backend: module`. The API workflow has been tested automatically. A full manual browser walkthrough
has not been performed. The old UI exposes Orders through its POST `order/refresh`
route; arbitrary Orders GET URLs under port 8080 can return 404.

## Repeat the automated booking test

```powershell
python docs/migration/verify_booking.py manual-check
python docs/migration/verify_booking_other.py manual-check
```

This logs in with the dedicated synthetic account, searches, books, pays, checks
the exact wallet debit, cancels and checks the quoted refund. It retains cancelled
orders and consumes the benchmark cancellation fee from the synthetic wallet.
Credentials remain in ignored `deployment/migration/.state/e2e/fixture.json`.
The fixture was provisioned in this workspace; preserve that file. Repeated runs
can encounter existing booking limits or exhaust that wallet.

## Isolated side-by-side comparisons

```powershell
python docs/migration/run_hybrid.py --comparisons
python docs/migration/verify_station.py
python docs/migration/verify_orders.py
python docs/migration/verify_order_other.py
python docs/migration/verify_config.py
python docs/migration/verify_seat_candidate.py
python docs/migration/verify_security.py
python docs/migration/verify_train.py
python docs/migration/verify_route.py
python docs/migration/verify_price.py
```

| Service | Legacy endpoint | Module endpoint |
| --- | --- | --- |
| Station | http://localhost:22345 | http://localhost:18081 |
| Orders | http://localhost:22031 | http://localhost:18082 |
| OrderOther | http://localhost:22032 | http://localhost:18084 |
| Config | http://localhost:25679 | http://localhost:18087 |
| Seat | http://localhost:28898 | http://localhost:18088 |
| Security | http://localhost:21188 | http://localhost:18090 |
| Train | http://localhost:24567 | http://localhost:18092 |
| Route | http://localhost:21178 | http://localhost:18094 |
| Price | http://localhost:26579 | http://localhost:18096 |

These use separate test databases with matched baseline data. The scripts exercise
both implementations and compare results, including writes. They do not route live
bookings to the isolated test databases. Extra JVMs can take a while to start.
The launcher starts the module comparison hosts one at a time. Comparison
containers may be stopped to reduce memory use; the launcher with
`--comparisons` restarts them.

## Rehearse Orders rollback

Switches have a brief maintenance window. Avoid booking during a switch.

```powershell
python docs/migration/hybrid_routing.py legacy orders
python docs/migration/verify_checkpoint.py --rollback
python docs/migration/hybrid_routing.py module orders
python docs/migration/verify_checkpoint.py
```

Run each command only after the previous one succeeds. Station stays in the
modulith throughout. The rollback check probes the disabled Orders writer using
only a synthetic order and verifies that it remains unchanged.

Manage this deployment with the migration scripts. Starting the retained original
Station/Orders/OrderOther containers or running the root Compose deployment can conflict with
the routers' ports and service identities. Do not remove Docker volumes or the
ignored `.state` directory. Preserve `ts-modulith/target/evidence` before Maven clean.

OrderOther can be rolled back independently with
`python docs/migration/hybrid_routing.py legacy orderother`; use `module orderother`
to return it. Its rollback backend is a local image with the legacy startup sample
order writer removed. See [the third-service report](order-other-results.md).

Config can be rolled back independently with
`python docs/migration/hybrid_routing.py legacy config`; use `module config` to
return it. `python docs/migration/verify_config_rollback.py` exercises this with
a disposable record, then restores module routing. See [the Config report](config-results.md).

Seat can be rolled back independently with
`python docs/migration/hybrid_routing.py legacy seat`; use `module seat` to
return it. `python docs/migration/verify_seat_rollback.py` rehearses this with
read-only availability calls, then restores module routing. The Seat API is
called directly by other services at port 18898; the UI gateway does not expose
`/api/v1/seatservice/**` on port 8080. See [the Seat report](seat-results.md).

Security can be rolled back independently with
`python docs/migration/hybrid_routing.py legacy security`; use
`module security` to return it. `python docs/migration/verify_security_rollback.py`
rehearses this with a disposable policy record, then restores module routing.
The Security API is called directly at port 11188 and requires a USER or ADMIN
token. See [the Security report](security-results.md).

Train can be rolled back independently with
`python docs/migration/hybrid_routing.py legacy train`; use `module train` to
return it. `python docs/migration/verify_train_rollback.py` rehearses this and
returns Train to module mode. See [the Train report](train-results.md).

Route can be rolled back independently with
`python docs/migration/hybrid_routing.py legacy route`; use `module route` to
return it. `python docs/migration/verify_route_rollback.py` rehearses this and
returns Route to module mode. See [the Route report](route-results.md).

Price can be rolled back independently with
`python docs/migration/hybrid_routing.py legacy price`; use `module price` to
return it. `python docs/migration/verify_price_rollback.py` rehearses this and
returns Price to module mode. See [the Price report](price-results.md).

For Price's isolated comparison, use
`python docs/migration/run_hybrid.py --price-comparison` to start only its test endpoints. Starting all comparison
hosts can use substantial memory.

Basic can be rolled back independently with
`python docs/migration/hybrid_routing.py legacy basic`; use `module basic` to
return it. `python docs/migration/verify_basic_rollback.py` rehearses this and
returns Basic to module mode. Basic has no database and no writes. See
[the Basic report](basic-results.md).

For Basic's live read-only comparison, run
`python docs/migration/run_hybrid.py --basic-comparison`, then
`python docs/migration/verify_basic.py` while Basic is on the legacy route.
After cutover, the comparison script must target the stopped legacy backend
separately; the completed 26-check evidence is in the build evidence directory.

Travel can be rolled back independently with
`python docs/migration/hybrid_routing.py legacy travel` and returned with
`python docs/migration/hybrid_routing.py module travel`.
`python docs/migration/verify_travel_rollback.py` rehearses a write handover
using a disposable trip and returns to module mode. For the isolated contract
comparison, run `python docs/migration/run_hybrid.py --travel-comparison`
then `python docs/migration/verify_travel.py`. See the
[Travel report](travel-results.md).

Travel2 can be rolled back independently with
`python docs/migration/hybrid_routing.py legacy travel2` and returned with
`python docs/migration/hybrid_routing.py module travel2`.
`python docs/migration/verify_travel2_rollback.py` rehearses its write handover
and returns to module mode. For side-by-side checks, run
`python docs/migration/run_hybrid.py --travel2-comparison` then
`python docs/migration/verify_travel2.py`. See the
[Travel2 report](travel2-results.md).

Route Plan can be rolled back independently with
`python docs/migration/hybrid_routing.py legacy routeplan` and returned with
`python docs/migration/hybrid_routing.py module routeplan`.
`python docs/migration/verify_route_plan_rollback.py` rehearses this and
returns to module mode. `python docs/migration/start_route_plan_candidate.py`
starts a read-only candidate for `python docs/migration/verify_route_plan.py`.
See the [Route Plan report](route-plan-results.md).

Travel Plan can be rolled back independently with
`python docs/migration/hybrid_routing.py legacy travelplan` and returned with
`python docs/migration/hybrid_routing.py module travelplan`.
`python docs/migration/verify_travel_plan_rollback.py` rehearses this and
returns to module mode. `python docs/migration/start_travel_plan_candidate.py`
starts a read-only candidate for `python docs/migration/verify_travel_plan.py`.
See the [Travel Plan report](travel-plan-results.md).

Contacts can be rolled back independently with
`python docs/migration/hybrid_routing.py legacy contacts` and returned with
`python docs/migration/hybrid_routing.py module contacts`.
`python docs/migration/verify_contacts_rollback.py` rehearses a write handover
and returns to module mode. On the browser's **Ticket Reserve â†’ Booking**
page, the contact lookup response should show `X-Contacts-Backend: module`.
See the [Contacts report](contacts-results.md).

Preserve can be rolled back independently with
`python docs/migration/hybrid_routing.py legacy preserve` and returned with
`python docs/migration/hybrid_routing.py module preserve`.
`python docs/migration/verify_preserve_rollback.py` rehearses this with full
synthetic booking, payment and cancellation on each side. Run
`python docs/migration/verify_booking.py preserve-ui-check --preserve-port 8080`
to exercise the gateway route. See the [Preserve report](preserve-results.md).

PreserveOther can be rolled back independently with `python docs/migration/hybrid_routing.py legacy preserveother` and returned with `python docs/migration/hybrid_routing.py module preserveother`. Run `python docs/migration/verify_preserve_other_rollback.py` for a full booking, payment and cancellation rehearsal. See the [PreserveOther report](preserve-other-results.md).

For a visible PreserveOther journey in **Ticket Reserve**, choose **Other**, `Nan Jing` to `Shang Hai`, and today or a future date. The default `Shang Hai` to `Su Zhou` selection has no Other journey in the current catalogue.

Execute can be rolled back independently with `python docs/migration/hybrid_routing.py legacy execute` and returned with `python docs/migration/hybrid_routing.py module execute`. `python docs/migration/verify_execute_rollback.py` verifies both order types. In the UI, use **Execute Flow ? Ticket Collect**, then **Enter Station** on a paid booking. Inspect `X-Execute-Backend: module` on the two Execute responses. See the [Execute report](execute-results.md).

WaitOrder is still pending because the local runtime has no WaitOrder container or its configured MySQL database.

Payment can be rolled back independently with `python docs/migration/hybrid_routing.py legacy payment` and returned with `python docs/migration/hybrid_routing.py module payment`. `python docs/migration/verify_payment_rollback.py` checks write ownership and continuity. For a direct check, call `http://localhost:19001/api/v1/paymentservice/welcome` with a valid JWT and inspect `X-Payment-Backend: module`. Port 8080 does not expose a generic Payment API route in the current UI NGINX configuration. See the [Payment report](payment-results.md).

Inside Payment can be rolled back independently with `python docs/migration/hybrid_routing.py legacy insidepayment` and returned with `python docs/migration/hybrid_routing.py module insidepayment`. `python docs/migration/verify_inside_payment_rollback.py` rehearses this with synthetic paid orders. Use **Order List â†’ Pay** and inspect the response header `X-InsidePayment-Backend: module` on `POST /api/v1/inside_pay_service/inside_payment`. `python docs/migration/verify_inside_payment_ui.py` runs the same browser-facing path with a disposable order. See the [Inside Payment report](inside-payment-results.md).

Cancel can be rolled back independently with `python docs/migration/hybrid_routing.py legacy cancel` and returned with `python docs/migration/hybrid_routing.py module cancel`. `python docs/migration/verify_cancel_rollback.py` rehearses both paths. Use **Order List â†’ Cancel** and inspect `X-Cancel-Backend: module` on the `GET /api/v1/cancelservice/cancel/{orderId}/{loginId}` response. `python docs/migration/verify_cancel_ui.py` runs the browser-facing path with a disposable paid order and verifies its refund. See the [Cancel report](cancel-results.md).

Rebook can be rolled back independently with `python docs/migration/hybrid_routing.py legacy rebook` and returned with `python docs/migration/hybrid_routing.py module rebook`. `python docs/migration/verify_rebook_rollback.py` rehearses both paths. Use **Order List â†’ Change**, choose a replacement train and confirm. Inspect `X-Rebook-Backend: module` on `POST /api/v1/rebookservice/rebook`; a higher fare also calls `POST /api/v1/rebookservice/rebook/difference`. `python docs/migration/verify_rebook_ui.py` checks a disposable changed order through port 8080. `python docs/migration/verify_rebook_workflows.py` checks refund, fare-difference payment and crossing from Orders to OrderOther with synthetic data. See the [Rebook report](rebook-results.md).

Assurance can be rolled back independently with `python docs/migration/hybrid_routing.py legacy assurance` and returned with `python docs/migration/hybrid_routing.py module assurance`. `python docs/migration/verify_assurance_rollback.py` rehearses both paths. On **Ticket Reserve**, inspect `GET /api/v1/assuranceservice/assurances/types` for HTTP 200 and `X-Assurance-Backend: module`. See the [Assurance report](assurance-results.md).

ConsignPrice can be rolled back independently with `python docs/migration/hybrid_routing.py legacy consignprice` and returned with `python docs/migration/hybrid_routing.py module consignprice`. `python docs/migration/verify_consign_price_rollback.py` rehearses its quote and configuration paths. See the [ConsignPrice report](consign-price-results.md).

Consign can be rolled back independently with `python docs/migration/hybrid_routing.py legacy consign` and returned with `python docs/migration/hybrid_routing.py module consign`. `python docs/migration/verify_consign_rollback.py` rehearses shared data and write ownership. On **Order List -> Consign**, inspect `X-Consign-Backend: module` on `PUT /api/v1/consignservice/consigns`. `python docs/migration/verify_consign_ui.py` checks that browser-facing path with a disposable shipment. See the [Consign report](consign-results.md).

Food Map can be rolled back independently with `python docs/migration/hybrid_routing.py legacy foodmap` and returned with `python docs/migration/hybrid_routing.py module foodmap`. The legacy image adds catalogue rows on startup; use `python docs/migration/verify_foodmap_rollback.py` to snapshot IDs, rehearse the switch and remove only the new rows. `python docs/migration/verify_foodmap_integration.py` checks the Food-to-Food Map menu path. Check the Food Map header on port 18855 directly. See the [Food Map report](foodmap-results.md).

Food can be rolled back independently with `python docs/migration/hybrid_routing.py legacy food` and returned with `python docs/migration/hybrid_routing.py module food`. Run `python docs/migration/verify_food_rollback.py` for a read-only rehearsal that restores module routing. On **Ticket Reserve -> Booking -> Need Food**, check the food menu response for `X-Food-Backend: module`. See the [Food report](food-results.md).

Notification can be rolled back independently with `python docs/migration/hybrid_routing.py legacy notification` and returned with `python docs/migration/hybrid_routing.py module notification`. Run `python docs/migration/verify_notification_rollback.py` for a read-only rehearsal. Check its direct port 17853; the running UI on port 8080 has no Notification API route or dedicated screen. See the [Notification report](notification-results.md).

Verification Code can be rolled back independently with `python docs/migration/hybrid_routing.py legacy verifycode` and returned with `python docs/migration/hybrid_routing.py module verifycode`. Run `python docs/migration/verify_verifycode_rollback.py` for a read-only rehearsal. Open the login dialog at http://localhost:8080/index.html, inspect the CAPTCHA image request to `/api/v1/verifycode/generate`, and check `X-VerifyCode-Backend: module`. The direct verification endpoint is on port 15678; the UI gateway does not expose it. See the [Verification Code report](verifycode-results.md).

Auth can be rolled back independently with `python docs/migration/hybrid_routing.py legacy auth` and returned with `python docs/migration/hybrid_routing.py module auth`. Run `python docs/migration/verify_auth_rollback.py` for a read-only login rehearsal. On the login dialog at http://localhost:8080/index.html, inspect the `POST /api/v1/users/login` response for `X-Auth-Backend: module` and `status: 1`. Existing signed tokens remain compatible. See the [Auth report](auth-results.md).

User can be rolled back independently with `python docs/migration/hybrid_routing.py legacy user` and returned with `python docs/migration/hybrid_routing.py module user`. Run `python docs/migration/verify_user_rollback.py` for a read-only rehearsal. To prove the User backend directly, inspect `GET http://localhost:8080/api/v1/userservice/users/fdse_microservice` for `X-User-Backend: module`. Admin User now calls User through its published module API; its independent rollback rehearsal is `python docs/migration/verify_admin_user_rollback.py`. On http://localhost:8080/admin_user.html, inspect `GET /api/v1/adminuserservice/users` for `X-AdminUser-Backend: module`. See the [User report](user-results.md) and [Admin User report](admin-user-results.md).

## Direct module calls checkpoint

Run `python docs/migration/verify_direct_modules_candidate.py` to start an isolated copy of the host. It checks the 45-module graph, login, both trip searches, and both booking paths with Assurance, Food and Consign using separate test databases. It also checks that Java source has no in-host HTTP client. After it passes, `python docs/migration/prepare_direct_modules.py` updates the hybrid host. Then run `python docs/migration/verify_checkpoint.py`, `python docs/migration/verify_booking.py direct-modules-live`, and `python docs/migration/verify_booking_other.py direct-modules-other-live`. The browser still uses HTTP through port 8080; response headers identify the routed module but cannot by themselves prove that calls *inside* the host are in-process.
