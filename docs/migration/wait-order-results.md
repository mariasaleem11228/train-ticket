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

Automatic reservation retries are enabled in the live hybrid. The replacement
worker claims due entries with a database lease, books through Preserve's
published Java API, and records the resulting order ID. A stable order ID and
MongoDB insert-if-absent make replay of one wait-list entry idempotent. Failed
attempts back off for five minutes; expired entries are closed. The isolated
retry candidate passed booking, replay, ownership, failure and expiry checks.
These checks do not prove seat allocation is collision-free across concurrent
ordinary bookings and wait-list retries; that needs a controlled load test.

Resume with `python docs/migration/run_hybrid.py`. Check the host using
`python docs/migration/verify_checkpoint.py` and
`python docs/migration/verify_wait_order_live.py`. The live WaitOrder database is
the Docker volume `station-migration_wait-order-data`. The isolated candidate
was stopped after testing to save memory. To re-run the retry test, inspect
`docs/migration/start_wait_order_retry_candidate.py` and use the separate
`wait_order_retry_candidate` schema and isolated Orders MongoDB database.
