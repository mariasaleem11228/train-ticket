package trainticket.assurance.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.*;
import trainticket.assurance.AssuranceOperations;
import java.util.UUID;

@RestController
@ConditionalOnProperty(name="modulith.assurance.enabled", havingValue="true")
@RequestMapping("/api/v1/assuranceservice")
class AssuranceController {
    private final AssuranceOperations assurance;
    AssuranceController(AssuranceOperations assurance) { this.assurance = assurance; }
    @GetMapping("/welcome") String welcome() { return "Welcome to [ Assurance Service ] !"; }
    @GetMapping("/assurances") Object all() { return assurance.all(); }
    @GetMapping("/assurances/types") Object types() { return assurance.types(); }
    @GetMapping("/assurances/assuranceid/{id}") Object byId(@PathVariable UUID id) { return assurance.byId(id); }
    @GetMapping("/assurance/orderid/{orderId}") Object byOrder(@PathVariable UUID orderId) { return assurance.byOrder(orderId); }
    @GetMapping("/assurances/{type}/{orderId}") Object create(@PathVariable int type, @PathVariable UUID orderId) { return assurance.create(type,orderId); }
    @PatchMapping("/assurances/{id}/{orderId}/{type}") Object modify(@PathVariable UUID id,@PathVariable UUID orderId,@PathVariable int type) { return assurance.modify(id,orderId,type); }
    @DeleteMapping("/assurances/assuranceid/{id}") Object deleteById(@PathVariable UUID id) { return assurance.deleteById(id); }
    @DeleteMapping("/assurances/orderid/{orderId}") Object deleteByOrder(@PathVariable UUID orderId) { return assurance.deleteByOrder(orderId); }
}
