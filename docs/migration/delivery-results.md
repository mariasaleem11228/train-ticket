# Delivery migration checkpoint

Delivery is business module 41 in the shared Spring Modulith host. It consumes
RabbitMQ's `food_delivery` queue and writes `orderId`, `foodName`, `storeName`, and
`stationName` to the dedicated `deliveryservice` MySQL database. It has no HTTP
controller, browser route, or `X-...-Backend` response header. A booking with food
is the UI action that can publish a Delivery message.

The legacy Delivery service was absent from the running Compose stack, so a live
legacy-to-module comparison or switch back to a legacy container was unavailable.
Before cutover, 15 pending live messages were copied without acknowledging them
to `deployment/migration/.state/backups/delivery-queue.json`. The isolated
candidate used `food_delivery_candidate` and a `delivery_candidate` schema; it
persisted a duplicate message once and left the live queue unchanged. Maven tests
and packaging passed. After enabling the live consumer, all 15 backed-up order
IDs appeared in `deliveryservice.delivery`, and the live queue drained. The full
hybrid checkpoint passed with 41 modules.

The module uses an upsert on `order_id` so redelivery does not create duplicate
rows. This is an intentional reliability change from the legacy repository's
ordinary save operation. The remaining 40 HTTP routes stayed on the shared host
during the Delivery cutover.

To inspect the current deployment:

```powershell
python docs/migration/verify_checkpoint.py
python docs/migration/verify_delivery_live.py
python docs/migration/delivery_ownership.py status
```

`verify_delivery_live.py` checks that all 15 messages from the saved pre-cutover
backlog are in MySQL, the queue is empty, and one module consumer owns it. To
stop or restart queue consumption without stopping the other modules, use
`python docs/migration/delivery_ownership.py pause` or `resume`. Pausing leaves
new messages in RabbitMQ; it does not route them to a legacy Delivery service.
The saved queue payloads provide recovery evidence if the Delivery database must
be restored.

Food Delivery was subsequently ported as module 42. TicketInfo and WaitOrder
remain outside this running hybrid.
