# Route Plan migration checkpoint

30 September 2026. Route Plan is the thirteenth Spring Modulith business module.
Its compatibility proxy keeps the original `ts-route-plan-service:14578`
identity. `X-RoutePlan-Backend: module` identifies the live backend. Travel Plan
is next in the migration sequence.

## Contract and implementation

The deployed service exposes `/welcome` and three POST endpoints under
`/routePlan`: `cheapestRoute`, `quickestRoute`, and `minStopStations`. It has no
database or writes. The module calls the published Station, Route, Travel, and
Travel2 Java APIs and preserves the deployed ranking results and response
fields. The still-remote Travel Plan microservice can call it through the
original service identity.

In the browser, **Advanced Search** calls Travel Plan's cheapest, quickest,
or minimum-stop endpoint; Travel Plan then calls Route Plan. The browser sees
Travel Plan's response headers, so use the direct Route Plan header check below
to confirm which backend handled that internal call.

The deployed service returns HTTP 500 for a past-date cheapest or quickest
search. The module returns HTTP 200 with an empty list for those inputs. The
side-by-side test records this deliberate difference. Both implementations
return HTTP 500 for a minimum-stops query with no direct journey; that case
needs a separate behavior fix after the remaining search modules are migrated.

## Evidence

- Maven module and architecture tests passed.
- `verify_route_plan.py` passed 22 comparisons across six station pairs and
  all three operations, including ranking of multiple journeys, empty results,
  and the recorded past-date difference.
- The still-remote Travel Plan service returned successful cheapest, quickest,
  and minimum-stop searches through Route Plan's migrated identity.
- `verify_route_plan_rollback.py` switched only Route Plan to the original
  legacy image, compared a ranking response, and returned it to the module.
- `verify_checkpoint.py` passed thirteen service routes, module dependencies,
  and retained synthetic orders.

## Resume and verify

```powershell
python docs/migration/run_hybrid.py
python docs/migration/verify_checkpoint.py
(Invoke-WebRequest http://localhost:14578/api/v1/routeplanservice/welcome -UseBasicParsing).Headers['X-RoutePlan-Backend']
```

The header should be `module`. Repeat the independent rollback rehearsal with
`python docs/migration/verify_route_plan_rollback.py`. To repeat the live
comparison, start a read-only candidate with
`python docs/migration/start_route_plan_candidate.py`, then run
`python docs/migration/verify_route_plan.py`.
