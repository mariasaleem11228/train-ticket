package trainticket.execute.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.*;
import trainticket.execute.ExecuteOperations;

@RestController
@ConditionalOnProperty(name="modulith.execute.enabled", havingValue="true")
@RequestMapping("/api/v1/executeservice")
class ExecuteController {
    private final ExecuteOperations execute;
    ExecuteController(ExecuteOperations execute) { this.execute=execute; }

    @GetMapping("/welcome") String welcome() { return "Welcome to [ Execute Service ] !"; }
    @CrossOrigin(origins="*")
    @GetMapping("/execute/execute/{orderId}") Object execute(@PathVariable String orderId) {
        return execute.execute(orderId);
    }
    @CrossOrigin(origins="*")
    @GetMapping("/execute/collected/{orderId}") Object collect(@PathVariable String orderId) {
        return execute.collect(orderId);
    }
}
