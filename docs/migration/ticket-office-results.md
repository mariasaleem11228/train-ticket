# Ticket Office migration checkpoint

Ticket Office is Spring Modulith business module 39. It is independent and uses the existing MongoDB `ticket-office.office` collection. The module reads that collection without startup seeding. Its region list comes from the JSON file in the deployed Node image, which differs from the checked-in source file.

The isolated candidate used separate MongoDB copies for Node and Java. Welcome, region list, all offices, specific and missing regions, and add, update, and delete responses matched. A live Mongo archive is saved under `deployment/migration/.state/backups/ticket-office.archive`.

The deployed Node image deletes and reloads all offices whenever it starts. The rollback backend therefore uses `train-ticket/ts-ticket-office-legacy:no-reseed`, built from the deployed image with only its startup seeding call removed. Direct restoration of the original image is blocked to protect writes made by the module. The compatibility proxy keeps `ts-ticket-office-service:16108` and supports module/legacy switching.

Run `python docs/migration/verify_checkpoint.py` for the full hybrid check and `python docs/migration/verify_ticket_office_rollback.py` to check that an office created by the module remains visible after switching to Node and back. The UI is `http://localhost:8080/old_index.html`, in the **Ticket Office List** section. `GET /office/getRegionList` and `POST /office/getSpecificOffices` should include `X-TicketOffice-Backend: module`.

Avatar has since moved to the shared host with its dlib detector packaged locally; see [Avatar results](avatar-results.md).
