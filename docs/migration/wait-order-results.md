# WaitOrder migration checkpoint

WaitOrder is module 44 in the shared Spring Modulith host. Its four legacy HTTP
paths are implemented on port 18080. It stores orders in a dedicated MySQL
database, checks duplicates, restricts calls to authenticated users, and expires
waiting orders after their deadline. The original WaitOrder service and database
were not running in this stack, so no production data was transferred.

The isolated candidate used a separate `wait_order_candidate` schema and passed
the module graph, authorization, create, duplicate, and list checks. The live
host passed its smoke test and the full migration checkpoint. TicketInfo live
contract checks and Delivery/Food Delivery live checks also passed after cutover.

Automatic reservation retries are **not enabled**. The legacy PollThread has a
reversed deadline comparison, calls `/api/v1/contactservice/preserve` rather
than Preserve's booking path, and changes status using account ID in place of
wait-order ID. A safe replacement needs booking idempotency, durable retry state,
and a service authorization strategy that survives JWT expiry. Until then,
WaitOrder accepts and expires wait-list entries but does not reserve a seat when
one becomes available. This is the remaining functional migration task.

Resume with `python docs/migration/run_hybrid.py`. Check the host using
`python docs/migration/verify_checkpoint.py` and
`python docs/migration/verify_wait_order_live.py`. The live WaitOrder database is
the Docker volume `station-migration_wait-order-data`. The isolated candidate
was stopped after testing to save memory. Start it with
`docker start wait-order-module-candidate` to compare on port 18144; its data is
in the same MySQL container's separate `wait_order_candidate` schema.
