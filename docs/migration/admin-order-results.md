# Admin Order migration checkpoint

Admin Order is Spring Modulith business module 35. Its published dependencies are Orders and OrderOther. It combines their order lists and sends changes to Orders for train numbers starting with `G` or `D`, and to OrderOther for other train numbers. The original service remains available for independent rollback through the Admin Order routing proxy.

The isolated candidate used copies of both order databases. Its ADMIN welcome and combined-list responses matched the deployed service. Anonymous and USER access were denied as before. Synthetic create, update, list, and delete flows passed for both order stores without changing live data. The module boundary test and Maven package passed.

Run `python docs/migration/verify_checkpoint.py` for the live route, host graph, and retained order checks. Run `python docs/migration/verify_admin_order_rollback.py` to rehearse module → legacy → module routing without writes. The browser screen is `http://localhost:8080/admin.html` after an ADMIN login. In DevTools, the `GET /api/v1/adminorderservice/adminorder` response should include `X-AdminOrder-Backend: module`.
