package trainticket.fooddelivery.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.*;
import trainticket.fooddelivery.FoodDeliveryOrder;

import java.util.Map;

@RestController
@ConditionalOnProperty(name="modulith.fooddelivery.enabled",havingValue="true")
@RequestMapping("/api/v1/fooddeliveryservice")
class FoodDeliveryController {
    private final FoodDeliveryApplicationService service;
    FoodDeliveryController(FoodDeliveryApplicationService service) { this.service=service; }

    @GetMapping("/welcome") String welcome() { return "Welcome to [ food delivery service ] !"; }
    @PostMapping("/orders") Object create(@RequestBody FoodDeliveryOrder order) { return service.create(order); }
    @DeleteMapping("/orders/d/{orderId}") Object delete(@PathVariable String orderId) {
        return service.delete(orderId);
    }
    @GetMapping("/orders/all") Object all() { return service.all(); }
    @GetMapping("/orders/store/{storeId}") Object byStore(@PathVariable String storeId) {
        return service.byStore(storeId);
    }
    @GetMapping("/orders/{orderId}") Object byId(@PathVariable String orderId) {
        return service.byId(orderId);
    }
    @PutMapping("/orders/tripid") Object tripId(@RequestBody Map<String,Object> body) {
        return service.update(String.valueOf(body.get("orderId")),
                old->old.withTripId(String.valueOf(body.get("tripId"))),"update tripId success");
    }
    @PutMapping("/orders/seatno") Object seatNo(@RequestBody Map<String,Object> body) {
        return service.update(String.valueOf(body.get("orderId")),
                old->old.withSeatNo(((Number)body.get("seatNo")).intValue()),"update seatNo success");
    }
    @PutMapping("/orders/dtime") Object deliveryTime(@RequestBody Map<String,Object> body) {
        return service.update(String.valueOf(body.get("orderId")),
                old->old.withDeliveryTime(String.valueOf(body.get("deliveryTime"))),
                "update deliveryTime success");
    }
}
