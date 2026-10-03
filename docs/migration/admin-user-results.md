# Admin User migration checkpoint

Admin User is Spring Modulith business module 36. It depends only on the published User API. Its compatibility route remains reversible independently of User and the other modules.

The isolated candidate used copies of the User and Auth databases. Its ADMIN welcome and user-list responses matched the deployed Admin User service. Anonymous and USER requests were denied. Synthetic admin create, update, duplicate rejection, and delete passed, including the linked Auth credential creation and removal. The module boundary test and Maven package passed.

Run `python docs/migration/verify_checkpoint.py` for the live route, graph, and retained-data checks. Run `python docs/migration/verify_admin_user_rollback.py` to rehearse module to legacy to module routing without writes. The browser screen is `http://localhost:8080/admin_user.html` after an ADMIN login. In DevTools, `GET /api/v1/adminuserservice/users` should include `X-AdminUser-Backend: module`.
