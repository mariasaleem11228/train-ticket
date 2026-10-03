package trainticket.travelplan.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.*;
import trainticket.travelplan.*;

@RestController
@ConditionalOnProperty(name="modulith.travel-plan.enabled", havingValue="true")
@RequestMapping("/api/v1/travelplanservice")
class TravelPlanController {
    private final TravelPlanOperations plans;
    TravelPlanController(TravelPlanOperations plans) { this.plans=plans; }
    @GetMapping("/welcome") String welcome() { return "Welcome to [ TravelPlan Service ] !"; }
    @PostMapping("/travelPlan/transferResult") Object transfer(@RequestBody TransferQuery query) {
        return plans.transfer(query);
    }
    @PostMapping("/travelPlan/cheapest") Object cheapest(@RequestBody TravelPlanQuery query) {
        return plans.cheapest(query);
    }
    @PostMapping("/travelPlan/quickest") Object quickest(@RequestBody TravelPlanQuery query) {
        return plans.quickest(query);
    }
    @PostMapping("/travelPlan/minStation") Object minimum(@RequestBody TravelPlanQuery query) {
        return plans.minimumStations(query);
    }
}
