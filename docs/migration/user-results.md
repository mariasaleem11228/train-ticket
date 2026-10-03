# User migration checkpoint

User is the thirty-first live Spring Modulith business module. The existing `ts-user-service:12342` address now routes to the shared host, with an independent switch back to the legacy service. Registration and deletion call Auth through its published `AuthOperations` interface. The module graph reports the single `user → auth` dependency.

The deployed User image uses MongoDB and UUIDs; the checked-in service source uses MySQL and string IDs. The deployed JAR and live responses were the parity baseline. Both the User and Auth Mongo databases were backed up before cutover. Candidate writes used copies of both databases, so registration and deletion did not change live accounts.

The isolated comparison passed 17 checks: the 31-module graph, existing and missing profile reads, registration, duplicate detection, Auth credential creation, profile update, and coordinated User/Auth deletion. Maven tests passed. After cutover the full hybrid checkpoint passed, and a User-only rollback rehearsal returned the route to legacy and back. A synthetic live registration reached the module, created a User profile and Auth credentials, allowed login, then removed both records. The port 8080 profile request returned `X-User-Backend: module`; the still-running Admin User service read its list through the unchanged User address.

To verify the backend directly, request `http://localhost:8080/api/v1/userservice/users/fdse_microservice` and check `X-User-Backend: module`. For a UI integration check, sign in as admin and open `http://localhost:8080/admin_user.html`; its list is provided by Admin User, which calls User. The UI request therefore identifies Admin User, while the direct User request proves the routed backend.

**Existing behavior to address later:** the User API and admin list include the stored profile password in responses, and a profile password update does not update Auth credentials. The module preserves those deployed contracts. User and Auth writes are across two Mongo databases without a shared transaction, as in the old service flow. A separate security and consistency change should remove exposed passwords and coordinate credential updates.

Run `python docs/migration/verify_checkpoint.py` for the full hybrid, `python docs/migration/verify_user_rollback.py` for the User-only read-only rollback rehearsal, or `python docs/migration/verify_user_live_registration.py` for a synthetic create/login/delete check. The next active service group in the plan is the admin facades, beginning with Admin Basic Info.
