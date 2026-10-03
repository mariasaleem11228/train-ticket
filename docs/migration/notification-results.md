# Notification migration checkpoint

Notification is the twenty-eighth live Spring Modulith business module. It keeps `/api/v1/notifyservice/**`, the existing `ts-notification-service:17853` identity, four email actions, and the `email` RabbitMQ consumer. It has no dependencies on other business modules. The module writes consumer delivery results to the existing Notification Mongo database and sends mail to the locally configured Mailpit server.

The Notification Mongo database was backed up before cutover (empty at this checkpoint). In isolation, the deployed service and module passed 18 comparisons: welcome, all four email endpoints, equal subjects and HTML, failed-address behavior, and one queued message consumed, saved, and delivered. The candidate used a separate Mongo database, `email_candidate` queue and Mailpit container, so it did not consume live messages or send live mail.

The host now reports 28 Spring Modulith modules. The full checkpoint passes. Notification-only rollback returned the route and queue ownership to the legacy service, confirmed one consumer and an inactive module, then switched back. A direct synthetic POST to port 17853 returned `true`, had `X-Notification-Backend: module`, and delivered one message to local Mailpit at `http://localhost:8025`. RabbitMQ reports one consumer on the live `email` queue after cutover. The live queue was not seeded with a test message; the queue-processing path was verified in isolation.

To verify without sending mail, request `http://localhost:17853/api/v1/notifyservice/welcome` and check `X-Notification-Backend: module`. Other containers can use the unchanged `ts-notification-service:17853` address. The running UI on port 8080 does not expose the Notification API, and Notification has no dedicated browser screen.

Run `python docs/migration/verify_checkpoint.py` for the full hybrid or `python docs/migration/verify_notification_rollback.py` to repeat the read-only, Notification-only rollback rehearsal. The latter briefly switches the email consumer to the legacy service and then restores the module.
