package trainticket.consignprice.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.*;
import trainticket.consignprice.ConsignPrice;
import trainticket.consignprice.ConsignPriceOperations;

@RestController
@ConditionalOnProperty(name="modulith.consign-price.enabled",havingValue="true")
@RequestMapping("/api/v1/consignpriceservice")
class ConsignPriceController {
    private final ConsignPriceOperations prices;
    ConsignPriceController(ConsignPriceOperations prices) { this.prices=prices; }
    @GetMapping("/welcome") String welcome() { return "Welcome to [ ConsignPrice Service ] !"; }
    @GetMapping("/consignprice/config") Object config() { return prices.config(); }
    @GetMapping("/consignprice/price") Object description() { return prices.description(); }
    @GetMapping("/consignprice/{weight}/{isWithinRegion}") Object quote(@PathVariable double weight,@PathVariable boolean isWithinRegion) {
        return prices.quote(weight,isWithinRegion);
    }
    @PostMapping("/consignprice") Object update(@RequestBody ConsignPrice config) { return prices.update(config); }
}
