# Voucher migration checkpoint

Voucher is Spring Modulith business module 37. It reads Orders and OrderOther through their published APIs and keeps voucher records in the existing MySQL table. The browser path remains `POST /getVoucher`; the compatibility proxy can route it independently to the original Python service or the module.

The deployed Python service and Java candidate were tested against separate copies of the live Voucher table. Both generated the same voucher response for an Orders record and an OrderOther record. Repeat requests returned the stored voucher, including when the request type changed. The Maven build and Spring Modulith boundary test passed. A copy of the live table was saved before cutover at `deployment/migration/.state/backups/voucher.sql`.

Run `python docs/migration/verify_checkpoint.py` for the live routes and 37-module graph. Run `python docs/migration/verify_voucher_rollback.py` for the module to legacy to module rehearsal using a cached synthetic voucher. In the browser, open `http://localhost:8080/client_order_list.html`, choose Print Voucher on an eligible order, and inspect `POST /getVoucher` for `X-Voucher-Backend: module`.

The live UI route created and reused a voucher for a retained synthetic order. The full checkpoint passed, then the cached voucher remained readable through module, legacy, and module again during the rollback rehearsal. The isolated candidate containers were stopped and removed after cutover.
