package trainticket.food.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.*;
import trainticket.food.FoodOrder;

import java.util.UUID;

@RestController
@ConditionalOnProperty(name="modulith.food.enabled",havingValue="true")
@RequestMapping("/api/v1/foodservice")
class FoodController {
    private final FoodApplicationService food;
    private final FoodDeliveryPublisher delivery;
    FoodController(FoodApplicationService food,FoodDeliveryPublisher delivery) {
        this.food=food;this.delivery=delivery;
    }
    @GetMapping("/welcome") String welcome() { return "Welcome to [ Food Service ] !"; }
    @GetMapping("/orders") Object all() { return food.all(); }
    @GetMapping("/orders/{orderId}") Object byOrder(@PathVariable UUID orderId) { return food.byOrder(orderId); }
    @PostMapping("/orders") Object create(@RequestBody FoodOrder order) { return food.create(order); }
    @PutMapping("/orders") Object update(@RequestBody FoodOrder order) { return food.update(order); }
    @DeleteMapping("/orders/{orderId}")
    Object delete(@PathVariable UUID orderId) { return food.delete(orderId); }
    @GetMapping("/foods/{date}/{startStation}/{endStation}/{tripId}")
    Object menu(@PathVariable String date,@PathVariable String startStation,
                @PathVariable String endStation,@PathVariable String tripId) {
        return food.menu(date,startStation,endStation,tripId);
    }
    @GetMapping("/test_send_delivery") boolean sendTest() { delivery.testMessage();return true; }
}
