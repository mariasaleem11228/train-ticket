# TrainTicket Spring Modulith Postman collection

Import [TrainTicket-Modulith.postman_collection.json](TrainTicket-Modulith.postman_collection.json) into Postman. It contains every HTTP method and URL pattern declared by the current host controllers: **272 mappings in 43 HTTP-facing modules**. The remaining two Spring Modulith modules, Delivery and Trip Catalog, have folders explaining that they have no HTTP controller. The collection is grouped in the same 45-module order as the Spring Modulith structure test.

## Set up

1. Start the hybrid deployment. The collection's `baseUrl` defaults to `http://localhost:18080`, the shared host, because the UI gateway on port 8080 does not expose every module API. Change it to `http://localhost:8080` only when testing a gateway-supported route.
2. Set collection variables `username` and `password` for a dedicated test account. POST bodies show literal example values such as `Shang Hai`, `Su Zhou`, `D1345`, and `2026-10-05` directly in Postman's Body tab. Change the date in a request body to a day with scheduled trips before sending it. If a URL uses the `date` or `travelDate` path variable and `date` is empty, the collection sets it to seven days from the current UTC date. Do not save real credentials or a JWT in a shared export. Admin-only requests use the separate `adminToken` variable; an ordinary user token cannot access them. Assurance requires the ordinary user role.
3. Send **auth → POST /api/v1/users/login**. On a successful response, its script saves `token` and `accountId`. If using CAPTCHA, set `verificationCode` and supply the browser's `YsbCaptcha` cookie; otherwise this collection leaves the field empty, as the existing migration test does.
4. Send **route → GET /routes** to populate `routeId`, and **contacts → GET /contacts/account/{accountId}** to populate `contactId` from the first result. Fill `orderId` after a booking, along with any remaining path variables. Every JSON body includes sample data, including array and map requests. Values such as `{{accountId}}`, `{{contactId}}`, `{{orderId}}`, and `{{routeId}}` remain variables because they must refer to records in your running system. The collection creates stable `newUserId` and `newOrderId` UUIDs on first use. Set `newPassword` before registering a synthetic user. Update and delete requests need the ID of an existing test record. For avatar POST, supply `avatarImageBase64` with an actual face image; that request is skipped while the variable is empty.

Each request checks for a 2xx HTTP response. Read the response body too: several endpoints return HTTP 200 with an application-level failure status. For the UI gateway, `X-<Module>-Backend: module` identifies routing; the direct host on port 18080 does not add that proxy header.

For **route → POST /api/v1/routeservice/routes**, first read **GET /routes** and confirm the sample station IDs `shanghai` and `nanjing` exist, or edit those literal IDs in the POST body. Its `stationList` and `distanceList` are comma-separated strings with the same number of entries. The POST is skipped when either route ID collection variable is empty, and its test also checks JSON `status: 1`. Use an isolated environment for route creation and clean up the new route afterward.

**Do not run the entire inventory as a workflow.** Some GET endpoints change data, and many requests need IDs created by earlier requests. Data-changing requests have a pre-request guard and are skipped unless collection variable `allowMutations` is `true`. Set it only for the specific request or module you intend to test in a disposable environment, then return it to `false`. This includes payment, cancellation, ticket entry, mail/queue test endpoints, and ordinary POST/PUT/PATCH/DELETE writes. Read-only POST searches and queries remain available.

For an automated end-to-end result, use the existing [standard booking script](../verify_booking.py) and [Other booking script](../verify_booking_other.py). They check order persistence, exact wallet debit/refund and status transitions with synthetic data. The [isolated direct-module test](../verify_direct_modules_candidate.py) also checks Assurance, Food and Consign records. Postman can exercise their public API effects; it cannot observe an in-process Java method call.

## Keep the collection current

After changing a controller, run:

```powershell
python docs/migration/export_postman_collection.py
python docs/migration/export_postman_collection.py --check
```

The exporter fails if a new controller module is missing from the 45-module manifest, if a method-level `@RequestMapping` needs special parsing, or if a method/URL appears twice. The `--check` command detects a stale collection.
