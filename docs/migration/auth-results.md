# Auth migration checkpoint

Auth is the thirtieth live Spring Modulith business module. Requests to the existing `ts-auth-service:12340` address now reach the shared host through an independent compatibility router. The legacy Auth container remains available for rollback. The module uses the deployed Auth Mongo database, preserves bcrypt password checks and the existing one-hour HS256 JWT format, and calls Verification Code through its unchanged service address.

The deployed Auth image uses MongoDB, while the checked-in `ts-auth-service` source uses MySQL. The deployed JAR, database shape and live responses were therefore used as the parity baseline. A backup of the three-record Auth Mongo database was saved at `deployment/migration/.state/backups/auth.archive` before cutover. Candidate write tests used an isolated database restored from that backup.

The isolated legacy/module comparison passed 22 checks: module graph, successful and failed login, signed token compatibility, another module accepting the token, admin list authorization, isolated registration, login after registration, and deletion. Maven tests and packaging passed. After cutover the full hybrid checkpoint passed, an Auth-only rollback rehearsal returned the route to legacy and back, and `POST http://localhost:8080/api/v1/users/login` returned HTTP 200 with `X-Auth-Backend: module` and `status: 1`.

To check from the UI, open `http://localhost:8080/index.html`, log in, and inspect `POST /api/v1/users/login` in DevTools Network. Confirm `X-Auth-Backend: module` and a successful response. The CAPTCHA image request should separately show `X-VerifyCode-Backend: module`. The live registration flow through User service was not exercised during this checkpoint; Auth registration and deletion were tested against the isolated database.

**Existing defect:** Verification Code returns `true` for a wrong code, so a successful login with a wrong code does not prove CAPTCHA protection. This migration preserves the deployed behavior and checks the Auth-to-Verification Code call. Fix CAPTCHA validation in a separate security change with login-flow tests. The deployed Auth API also includes password hashes in its admin list response; the module preserves that response shape for compatibility.

Run `python docs/migration/verify_checkpoint.py` for the full checkpoint or `python docs/migration/verify_auth_rollback.py` for the Auth-only rollback rehearsal. User is next in the identity stage.
