package trainticket.waitorder.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.*;

@RestController
@ConditionalOnProperty(name="modulith.wait-order.enabled", havingValue="true")
@RequestMapping("/api/v1/waitorderservice")
class WaitOrderController {
    private final WaitOrderService service;
    WaitOrderController(WaitOrderService service) { this.service=service; }

    @GetMapping("/welcome") String welcome() { return "Welcome to [ Wait Order Service ] !"; }
    @PostMapping("/order") Object create(@RequestBody WaitOrderRequest request) { return service.create(request); }
    @GetMapping("/orders") Object all() { return service.list(false); }
    @GetMapping("/waitlistorders") Object waiting() { return service.list(true); }
}
