package trainticket.consign.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.*;
import trainticket.consign.ConsignOperations;
import trainticket.consign.ConsignRequest;
import java.util.UUID;

@RestController
@ConditionalOnProperty(name="modulith.consign.enabled",havingValue="true")
@RequestMapping("/api/v1/consignservice")
class ConsignController {
    private final ConsignOperations consign;
    ConsignController(ConsignOperations consign) { this.consign=consign; }
    @GetMapping("/welcome") String welcome() { return "Welcome to [ Consign Service ] !"; }
    @PostMapping("/consigns") Object create(@RequestBody ConsignRequest body) { return consign.create(body); }
    @PutMapping("/consigns") Object update(@RequestBody ConsignRequest body) { return consign.update(body); }
    @GetMapping("/consigns/account/{id}") Object byAccount(@PathVariable UUID id) { return consign.byAccount(id); }
    @GetMapping("/consigns/order/{id}") Object byOrder(@PathVariable UUID id) { return consign.byOrder(id); }
    @GetMapping("/consigns/{consignee}") Object byConsignee(@PathVariable String consignee) { return consign.byConsignee(consignee); }
}
