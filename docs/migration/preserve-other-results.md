# PreserveOther migration checkpoint ? 1 October 2026

PreserveOther is the seventeenth business module in the shared Spring Modulith host. The compatibility proxy retains `ts-preserve-other-service:14569` and routes the original `/api/v1/preserveotherservice/**` API to the module. The live route is in `module` mode; the original container and a separately managed legacy instance remain available for rollback. `X-PreserveOther-Backend: module` identifies the active route.

The module coordinates the published Security, Contacts, Travel2, Station, Seat and OrderOther APIs in-process. TicketInfo, User, Assurance, Food and Consign remain remote. PreserveOther writes require both `PRESERVE_OTHER_WRITES_ENABLED=true` and `ownership.json` permitting `preserveother`. The isolated candidate used a separate OrderOther database. The live `ts` OrderOther `orders` collection was backed up to ignored `deployment/migration/.state/backups/preserve-other-orders.archive` before cutover.

## Verification

- Maven package and Spring Modulith boundary verification passed with 17 modules.
- Candidate matched the legacy welcome and missing-contact responses. It booked first- and second-class seats into an isolated OrderOther database.
- A synthetic baseline and module booking each completed search, booking, wallet payment, refund quote, cancellation and wallet refund. Thirteen stable order fields matched.
- Switching only PreserveOther to legacy blocked direct module writes. A full legacy booking/payment/cancellation passed, then the route returned to the module and the same workflow passed again.
- A booking through the browser-facing gateway on port 8080 passed the same sequence. `python docs/migration/verify_checkpoint.py` confirmed all 17 modules, routes and retained synthetic orders.

Evidence is under ignored `ts-modulith/target/evidence/`: `preserve-other-candidate.json`, `booking-other-preserve-other-{baseline,module,rollback,return,ui-route}.json`, `preserve-other-orders.json`, and `preserve-other-rollback.json`. Preserve this directory and `.state` before cleaning builds.

## Resume and inspect

```powershell
python docs/migration/run_hybrid.py
python docs/migration/verify_checkpoint.py
(Invoke-WebRequest http://localhost:14569/api/v1/preserveotherservice/welcome -UseBasicParsing).Headers['X-PreserveOther-Backend']
```

For a browser check, use **Ticket Reserve**, select **Other** train type, set **Starting Place** to `Nan Jing`, **Terminal Place** to `Shang Hai`, choose today or a future date, click **Search**, and then click **Booking** on the returned journey. The default `Shang Hai` to `Su Zhou` selection has no Other journey in the current catalogue. Inspect the `POST /api/v1/preserveotherservice/preserveOther` response header in DevTools. To rehearse a synthetic booking through port 8080, run `python docs/migration/verify_booking_other.py preserve-other-ui-check --preserve-other-port 8080`. This creates and then cancels a test order, leaving audit evidence.

Rollback: `python docs/migration/hybrid_routing.py legacy preserveother`; return with `python docs/migration/hybrid_routing.py module preserveother`. `python docs/migration/verify_preserve_other_rollback.py` tests both directions.

The assurance, food and consign optional branches were carried across but have not received an end-to-end comparison. Concurrent bookings, retries, partial failures and performance remain future acceptance work. Next planned service: **WaitOrder**.

The 1 October 2026 UI follow-up found that the browser posts `startPlace` and a `yyyy-MM-dd HH:mm:ss` departure time, while the first Travel/Travel2 module implementation accepted `startingPlace` and date-only input. Both modules now accept the browser format as well. A live port-8080 check returned HTTP 200, `X-Travel2-Backend: module`, and one journey for `Nan Jing` to `Shang Hai`; the default `Shang Hai` to `Su Zhou` route returned zero journeys with HTTP 200. The full migration checkpoint passed after the host upgrade.
