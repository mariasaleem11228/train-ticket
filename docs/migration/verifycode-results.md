# Verification Code migration checkpoint

Verification Code is the twenty-ninth live Spring Modulith business module. Its existing `ts-verification-code-service:15678` address now routes to the shared host, while the legacy container remains available for an independent rollback. The module has no dependencies on other business modules and stores CAPTCHA codes in memory; there was no database to back up.

The deployed legacy service and isolated module passed 16 comparisons covering the 29-module graph, JPEG dimensions, response content type, session and CAPTCHA cookies, cookie rotation, and verification responses. Maven tests and package build passed. The full hybrid checkpoint passed after cutover, and a rollback rehearsal served the image and verification endpoint from legacy before returning to the module. The browser gateway's `/api/v1/verifycode/generate` returned HTTP 200, a JPEG, and `X-VerifyCode-Backend: module`.

To check the UI, open `http://localhost:8080/index.html` and show the login dialog. In DevTools Network, select the `/api/v1/verifycode/generate` image request. Confirm HTTP 200, an image, and `X-VerifyCode-Backend: module`. The direct `/api/v1/verifycode/verify/{code}` endpoint is available at `http://localhost:15678`; the port 8080 UI gateway does not expose that endpoint.

**Known legacy defect:** the deployed verification controller returns `true` for incorrect codes and even without an existing CAPTCHA cookie. This port preserves that wire behavior for parity; it does not establish that login's CAPTCHA validation is secure. The bug should be fixed in a separate, coordinated security change with end-to-end login tests. Codes already issued by the legacy process are not transferred to the module, so refresh the CAPTCHA image after a route switch.

Run `python docs/migration/verify_checkpoint.py` for the full checkpoint, or `python docs/migration/verify_verifycode_rollback.py` for the Verification Code-only rollback rehearsal. Next in the identity stage is Auth, subject to an isolated dependency and login-flow comparison.
