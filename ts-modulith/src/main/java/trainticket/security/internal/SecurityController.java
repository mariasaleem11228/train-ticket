package trainticket.security.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.*;
import trainticket.security.SecurityConfig;
import trainticket.security.SecurityOperations;

@RestController
@ConditionalOnProperty(name="modulith.security.enabled", havingValue="true")
@RequestMapping("/api/v1/securityservice")
class SecurityController {
    private final SecurityOperations security;
    SecurityController(SecurityOperations security) { this.security = security; }
    @GetMapping("/welcome") String welcome() { return "welcome to [Security Service]"; }
    @CrossOrigin(origins="*") @GetMapping("/securityConfigs") Object all() { return security.all(); }
    @CrossOrigin(origins="*") @PostMapping("/securityConfigs") Object create(@RequestBody SecurityConfig body) {
        return security.create(body);
    }
    @CrossOrigin(origins="*") @PutMapping("/securityConfigs") Object update(@RequestBody SecurityConfig body) {
        return security.update(body);
    }
    @CrossOrigin(origins="*") @DeleteMapping("/securityConfigs/{id}") Object delete(@PathVariable String id) {
        return security.delete(id);
    }
    @CrossOrigin(origins="*") @GetMapping("/securityConfigs/{accountId}") Object check(@PathVariable String accountId) {
        return security.check(accountId);
    }
}
