package trainticket.route.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.*;
import trainticket.route.RouteInfo;
import trainticket.route.RouteOperations;

@RestController
@ConditionalOnProperty(name="modulith.route.enabled", havingValue="true")
@RequestMapping("/api/v1/routeservice")
class RouteController {
    private final RouteOperations routes;
    RouteController(RouteOperations routes) { this.routes=routes; }
    @GetMapping("/welcome") String welcome() { return "Welcome to [ Route Service ] !"; }
    @GetMapping("/routes") Object all() { return routes.all(); }
    @GetMapping("/routes/{id}") Object find(@PathVariable String id) { return routes.find(id); }
    @GetMapping("/routes/{start}/{end}") Object between(@PathVariable String start, @PathVariable String end) {
        return routes.between(start,end);
    }
    @PostMapping("/routes") Object save(@RequestBody RouteInfo info) { return routes.save(info); }
    @DeleteMapping("/routes/{id}") Object delete(@PathVariable String id) { return routes.delete(id); }
}
