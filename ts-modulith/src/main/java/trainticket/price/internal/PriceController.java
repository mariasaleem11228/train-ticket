package trainticket.price.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import trainticket.price.PriceConfig;
import trainticket.price.PriceOperations;

@RestController
@ConditionalOnProperty(name="modulith.price.enabled",havingValue="true")
@RequestMapping("/api/v1/priceservice")
class PriceController {
    private final PriceOperations prices;
    PriceController(PriceOperations prices) { this.prices=prices; }
    @GetMapping("/prices/welcome") String welcome() { return "Welcome to [ Price Service ] !"; }
    @GetMapping("/prices") Object all() { return prices.all(); }
    @GetMapping("/prices/{routeId}/{trainType}") Object find(@PathVariable String routeId,@PathVariable String trainType) {
        return prices.find(routeId,trainType);
    }
    @PostMapping("/prices") ResponseEntity<?> create(@RequestBody PriceConfig config) {
        return ResponseEntity.status(201).body(prices.create(config));
    }
    @PutMapping("/prices") Object update(@RequestBody PriceConfig config) { return prices.update(config); }
    @DeleteMapping("/prices") Object delete(@RequestBody PriceConfig config) { return prices.delete(config); }
}
