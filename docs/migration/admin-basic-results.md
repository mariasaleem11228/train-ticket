# Admin Basic Info migration checkpoint

Admin Basic Info is the thirty-second live Spring Modulith business module. It is a stateless administration facade over published Contacts, Station, Train, Config and Price APIs. The existing `ts-admin-basic-info-service:18767` address now has an independent legacy/module switch. Spring Modulith verifies exactly those five dependencies.

The deployed JAR and live responses were the contract baseline. An isolated candidate matched all five catalogue reads and checked anonymous, USER and ADMIN access. Against copied Mongo databases, it passed create, update, delete and persistence checks for each catalogue. The legacy JAR accepts station and price DELETE requests with JSON bodies; the UI sends IDs in the URL. The module supports both shapes.

Maven tests, the 32-module hybrid checkpoint and a read-only Admin Basic Info rollback rehearsal passed. The gateway returned HTTP 200, 13 stations and `X-AdminBasic-Backend: module` for the station catalogue. The candidate container was removed after testing; isolated database copies remain under `ts-admin-basic-candidate` in the five provider Mongo containers.

For a browser check, sign in as an administrator and open **Admin Panel → Stations** (`http://localhost:8080/admin_station.html`). In DevTools Network, inspect `GET /api/v1/adminbasicservice/adminbasic/stations` for `X-AdminBasic-Backend: module`. The same header should appear on **Contacts**, **Trains**, **Configs** and **Prices** admin screens. The isolated candidate exercised their write paths; the live cutover verification was read-only.

Run `python docs/migration/verify_checkpoint.py` for the full stack or `python docs/migration/verify_admin_basic_rollback.py` for this route's rollback rehearsal. Next in the planned sequence: Admin Route, which depends on the already migrated Route catalogue.
