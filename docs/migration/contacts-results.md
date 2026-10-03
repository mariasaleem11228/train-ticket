# Contacts migration checkpoint

1 October 2026. Contacts is the fifteenth Spring Modulith business module.
The compatibility proxy retains `ts-contacts-service:12347` and sends live
requests to the host. `X-Contacts-Backend: module` identifies the backend.
Preserve is the next service in the migration sequence.

## Contract and storage

The module implements the deployed Contacts API: list, account lookup, ID
lookup, create, admin create, update, delete and welcome. It uses the existing
`ts-contacts-mongo` database with Java legacy UUID encoding. The checked-in
Contacts source targets MySQL, but the deployed 0.2.0 image uses MongoDB;
the deployed image and database were the contract for this migration.

Writes require both `CONTACTS_WRITES_ENABLED=true` and Contacts ownership in
the shared ownership file. The old service is stopped in module mode. The
collection was backed up at
`deployment/migration/.state/backups/contacts.archive` before cutover.

## Evidence

- Maven tests passed, including Spring Modulith's 15-module graph and the
  Contacts architecture boundary.
- Eleven read comparisons matched the live deployed service, including all
  existing contacts, account lookups, and missing-record cases.
- Twelve isolated write checks passed against legacy and module databases:
  create, account lookup, duplicate, update, delete and post-delete lookup.
- A disposable contact survived module-to-legacy-to-module rollback. The
  inactive module rejected a write, and the test contact was removed.
- The full hybrid checkpoint passed after cutover. A request through port
  8080 returned HTTP 200 with `X-Contacts-Backend: module`.
- The existing synthetic booking, payment and cancellation flows passed for
  both Preserve and PreserveOther while they called Contacts through its
  original service identity. Their cancelled test orders remain in the
  ignored fixture for checkpoint checks.

## Browser and resume checks

Open **Ticket Reserve**, search for a trip and click **Booking**. On the
`client_ticket_book.html` page, inspect the Network request to
`/api/v1/contactservice/contacts/account/{accountId}`. Its response should
show `X-Contacts-Backend: module`. Adding a contact on that page calls
`POST /api/v1/contactservice/contacts`; this is a live write, so use a
disposable contact if you test it.

```powershell
python docs/migration/run_hybrid.py
python docs/migration/verify_checkpoint.py
python docs/migration/verify_contacts_rollback.py
(Invoke-WebRequest http://localhost:12347/api/v1/contactservice/contacts/welcome -UseBasicParsing).Headers['X-Contacts-Backend']
```

The last command should return `module`. To repeat the read comparison,
start `python docs/migration/start_contacts_candidate.py`, route Contacts to
legacy temporarily, and run `python docs/migration/verify_contacts.py`.
Return Contacts to module mode afterward.
