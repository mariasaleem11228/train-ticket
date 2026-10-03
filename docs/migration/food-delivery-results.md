# Food Delivery migration checkpoint

Food Delivery is Spring Modulith business module 42. Its legacy HTTP API is
implemented at `/api/v1/fooddeliveryservice` in the shared host. It uses Food
Map's published Java API to look up a station food store and calculate the
delivery fee from catalogue prices. It stores orders in a dedicated
`fooddeliveryservice` MySQL database and has its own write-ownership gate.

The following legacy endpoints are implemented: welcome; create, delete, list,
get by ID, and get by store; and updates to trip ID, seat number, and delivery
time. The isolated candidate used a separate `food_delivery_candidate` schema.
Its checks covered every operation, missing food, and a deliberately false
client-supplied price: a Hamburger priced at 5 plus the store's 20 delivery fee
returned 25. Maven tests and packaging passed. After cutover, the same pricing,
CRUD, and disabled-writer checks passed on the live host. The full hybrid
checkpoint passed with 42 modules, and Delivery's queue consumer stayed active.

The legacy Food Delivery container and its MySQL database were absent from this
running stack. There was no live legacy database to import or side-by-side
response to compare. The module starts with an empty dedicated database, and
the isolated test orders were removed. The source service's data model was
adapted to a single SQL table with serialized food items, so importing a legacy
JPA database later would need an explicit conversion.

There is no current browser screen for Food Delivery. The running port 8080 UI
proxy has no route for this service; use the shared host's direct port:

```powershell
Invoke-WebRequest http://localhost:18080/api/v1/fooddeliveryservice/welcome -UseBasicParsing
python docs/migration/verify_food_delivery_live.py
python docs/migration/verify_checkpoint.py
```

The first command can also be opened in a browser. The second creates and
deletes a synthetic order and briefly pauses only Food Delivery writes to
confirm the 503 gate. To manually pause writes, set `fooddelivery` to
`maintenance` in `deployment/migration/.state/ownership/ownership.json`; set it
back to `module` to resume. There is no runnable legacy Food Delivery container
to receive writes during a pause.

TicketInfo and WaitOrder remain unported. TicketInfo is still running and serves
the Travel and booking modules; WaitOrder is absent from the running stack.
