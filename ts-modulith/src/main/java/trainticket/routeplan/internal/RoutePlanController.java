package trainticket.routeplan.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.*;
import trainticket.routeplan.RoutePlanInfo;
import trainticket.routeplan.RoutePlanOperations;

@RestController
@ConditionalOnProperty(name="modulith.route-plan.enabled", havingValue="true")
@RequestMapping("/api/v1/routeplanservice")
class RoutePlanController {
    private final RoutePlanOperations plans;
    RoutePlanController(RoutePlanOperations plans) { this.plans=plans; }
    @GetMapping("/welcome") String welcome() { return "Welcome to [ RoutePlan Service ] !"; }
    @PostMapping("/routePlan/cheapestRoute") Object cheapest(@RequestBody RoutePlanInfo info) {
        return plans.cheapest(info);
    }
    @PostMapping("/routePlan/quickestRoute") Object quickest(@RequestBody RoutePlanInfo info) {
        return plans.quickest(info);
    }
    @PostMapping("/routePlan/minStopStations") Object minimumStops(@RequestBody RoutePlanInfo info) {
        return plans.minimumStops(info);
    }
}
