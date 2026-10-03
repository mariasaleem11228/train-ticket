package trainticket.adminorder;

import java.util.ArrayList;
import java.util.List;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.*;
import trainticket.orders.Order;
import trainticket.orders.OrderOperations;

/** Admin facade over the two published order APIs. */
@RestController
@RequestMapping("/api/v1/adminorderservice")
@ConditionalOnProperty(name = "modulith.adminorder.enabled", havingValue = "true")
class AdminOrderController {
    private final OrderOperations orders;
    private final trainticket.orderother.OrderOtherOperations other;

    AdminOrderController(OrderOperations orders, trainticket.orderother.OrderOtherOperations other) {
        this.orders = orders;
        this.other = other;
    }

    record Response(int status, String msg, Object data) { }

    @GetMapping("/welcome") String welcome() { return "Welcome to [Admin Order Service] !"; }

    @GetMapping("/adminorder") Response all() {
        List<Object> values = new ArrayList<>();
        var first = orders.getAllOrders();
        var second = other.getAllOrders();
        if (first.getStatus() == 1 && first.getData() instanceof List<?> list) values.addAll(list);
        if (second.getStatus() == 1 && second.getData() instanceof List<?> list) values.addAll(list);
        return new Response(1, "Get the orders successfully!", values);
    }

    @PostMapping("/adminorder") Object create(@RequestBody Order value) {
        return fast(value.getTrainNumber()) ? orders.addNewOrder(value) : other.addNewOrder(toOther(value));
    }

    @PutMapping("/adminorder") Object update(@RequestBody Order value) {
        return fast(value.getTrainNumber()) ? orders.updateOrder(value) : other.updateOrder(toOther(value));
    }

    @DeleteMapping("/adminorder/{id}/{trainNumber}") Object delete(@PathVariable String id,
                                                                   @PathVariable String trainNumber) {
        return fast(trainNumber) ? orders.deleteOrder(id) : other.deleteOrder(id);
    }

    private boolean fast(String trainNumber) {
        return trainNumber.startsWith("G") || trainNumber.startsWith("D");
    }

    private trainticket.orderother.Order toOther(Order value) {
        var result = new trainticket.orderother.Order();
        result.setId(value.getId());
        result.setBoughtDate(value.getBoughtDate());
        result.setTravelDate(value.getTravelDate());
        result.setTravelTime(value.getTravelTime());
        result.setAccountId(value.getAccountId());
        result.setContactsName(value.getContactsName());
        result.setDocumentType(value.getDocumentType());
        result.setContactsDocumentNumber(value.getContactsDocumentNumber());
        result.setTrainNumber(value.getTrainNumber());
        result.setCoachNumber(value.getCoachNumber());
        result.setSeatClass(value.getSeatClass());
        result.setSeatNumber(value.getSeatNumber());
        result.setFrom(value.getFrom());
        result.setTo(value.getTo());
        result.setStatus(value.getStatus());
        result.setPrice(value.getPrice());
        return result;
    }
}
