# Preserve migration checkpoint

1 October 2026. Preserve is the sixteenth Spring Modulith business module.
The compatibility proxy keeps `ts-preserve-service:14568` and routes booking
requests to the shared host. `X-Preserve-Backend: module` identifies the live
backend. PreserveOther is next in the planned sequence.

## Implementation

The deployed service exposes `/welcome` and `POST /preserve`. The module uses
published APIs from Security, Contacts, Travel, Station, Seat and Orders.
TicketInfo, User, Assurance, Food and Consign still run as microservices and
are reached through explicit HTTP adapters. The deployed image builds a
notification but does not send it; the module preserves that behavior.

Preserve has no database of its own. Its booking writes create Orders records,
and the live `ts.orders` collection was backed up before cutover at
`deployment/migration/.state/backups/preserve-orders.archive`. The module
checks its own write-ownership gate before calling any writer. During rollback,
the inactive module returns HTTP 503 for booking POSTs.

## Evidence

- Maven tests and Spring Modulith verification passed for sixteen modules.
- The isolated candidate matched the deployed welcome and missing-contact
  responses, then booked second and first class into a separate Orders database.
- The deployed Preserve baseline and module each completed a synthetic booking,
  payment and cancellation. Thirteen stable fields of their Orders records
  matched, including fare, route, travel time and status. Seat number and
  generated timestamps/IDs vary by design.
- The independent rollback rehearsal completed a legacy booking, payment and
  cancellation, confirmed the inactive module rejected writes, then completed
  another booking after returning to module mode.
- The same flow passed through the browser-facing gateway at port 8080. A
  safe missing-contact POST there returned `X-Preserve-Backend: module`.
- The full hybrid checkpoint passed after cutover and rollback.

Optional insurance, food and consign selections have been mapped to the
deployed remote API paths and payloads. Their write paths have not been run
end to end in this checkpoint; exercise them with isolated ancillary data
before treating those options as fully characterized.

## Browser and resume checks

Open **Ticket Reserve**, choose a journey and click **Booking**. On the
booking page, submitting a booking calls
`POST /api/v1/preserveservice/preserve`; its Network response should include
`X-Preserve-Backend: module`. This creates a live order, so use the synthetic
test below if you want a booking that is paid and cancelled automatically.

```powershell
python docs/migration/run_hybrid.py
python docs/migration/verify_checkpoint.py
python docs/migration/verify_booking.py preserve-ui-check --preserve-port 8080
python docs/migration/verify_preserve_rollback.py
```

`verify_preserve_rollback.py` returns Preserve to module mode. To rerun the
isolated candidate test, start `python docs/migration/start_preserve_candidate.py`
and then run `python docs/migration/verify_preserve_candidate.py` while the
original legacy service is available for the safe comparison case.
