# Travel Plan migration checkpoint

1 October 2026. Travel Plan is the fourteenth Spring Modulith business module.
The proxy retains the original `ts-travel-plan-service:14322` identity;
`X-TravelPlan-Backend: module` identifies the live backend. Contacts is next.

## Contract and implementation

The deployed service exposes `/welcome`, three Advanced Search ranking POSTs
(`cheapest`, `quickest`, `minStation`), and `transferResult`. It has no database
or writes. The module uses published APIs from Station, Seat, Travel, Travel2,
and Route Plan. It preserves the deployed response fields, station names and
seat counts. The browser's **Advanced Search** page calls Travel Plan through
port 8080, where its response carries `X-TravelPlan-Backend: module`.

## Evidence

- Maven module and architecture tests passed. The candidate host reported
  fourteen business modules and the intended dependencies.
- `verify_travel_plan.py` passed 26 side-by-side checks across six station
  pairs, three ranking modes, past dates, and three transfer journeys.
- Advanced Search requests through port 8080 returned HTTP 200 and
  `X-TravelPlan-Backend: module` after cutover.
- `verify_travel_plan_rollback.py` switched only Travel Plan to its original
  image, compared a ranking response, and returned it to module mode.
- `verify_checkpoint.py` passed fourteen service routes, module dependencies,
  and retained synthetic orders.

## Resume and verify

```powershell
python docs/migration/run_hybrid.py
python docs/migration/verify_checkpoint.py
(Invoke-WebRequest http://localhost:14322/api/v1/travelplanservice/welcome -UseBasicParsing).Headers['X-TravelPlan-Backend']
```

The header should be `module`. Repeat rollback with
`python docs/migration/verify_travel_plan_rollback.py`. To compare again,
start a read-only candidate with
`python docs/migration/start_travel_plan_candidate.py` and run
`python docs/migration/verify_travel_plan.py`.
