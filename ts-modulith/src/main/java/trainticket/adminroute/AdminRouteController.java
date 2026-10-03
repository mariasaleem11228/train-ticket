package trainticket.adminroute;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.*;
import trainticket.route.RouteInfo;
import trainticket.route.RouteOperations;

/** Admin facade over the published Route catalogue operations. */
@RestController
@RequestMapping("/api/v1/adminrouteservice")
@ConditionalOnProperty(name = "modulith.adminroute.enabled", havingValue = "true")
class AdminRouteController {
    private final RouteOperations routes;

    AdminRouteController(RouteOperations routes) { this.routes = routes; }

    @GetMapping("/welcome") String welcome() { return "Welcome to [ AdminRoute Service ] !"; }
    @GetMapping("/adminroute") Object all() { return routes.all(); }
    @PostMapping("/adminroute") Object save(@RequestBody RouteInfo info) { return routes.save(info); }
    @DeleteMapping("/adminroute/{id}") Object delete(@PathVariable String id) { return routes.delete(id); }
}
