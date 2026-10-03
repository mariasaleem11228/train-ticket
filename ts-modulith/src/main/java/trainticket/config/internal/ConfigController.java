package trainticket.config.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import trainticket.config.Config;
import trainticket.config.ConfigOperations;

@RestController
@ConditionalOnProperty(name="modulith.config.enabled", havingValue="true")
@RequestMapping("/api/v1/configservice")
class ConfigController {
    private final ConfigOperations config;
    ConfigController(ConfigOperations config) { this.config = config; }

    @GetMapping("/welcome") String welcome() { return "Welcome to [ Config Service ] !"; }
    @CrossOrigin(origins="*") @GetMapping("/configs") Object all() { return config.all(); }
    @CrossOrigin(origins="*") @GetMapping("/configs/{configName}") Object find(@PathVariable String configName) {
        return config.find(configName);
    }
    @CrossOrigin(origins="*") @PostMapping("/configs") ResponseEntity<?> create(@RequestBody Config body) {
        return ResponseEntity.status(201).body(config.create(body));
    }
    @CrossOrigin(origins="*") @PutMapping("/configs") Object update(@RequestBody Config body) {
        return config.update(body);
    }
    @CrossOrigin(origins="*") @DeleteMapping("/configs/{configName}") Object delete(@PathVariable String configName) {
        return config.delete(configName);
    }
}
