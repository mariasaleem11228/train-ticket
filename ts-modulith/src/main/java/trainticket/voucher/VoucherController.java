package trainticket.voucher;

import java.util.Date;
import java.util.Map;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;
import trainticket.orders.OrderOperations;
import trainticket.orderother.OrderOtherOperations;

@RestController
@ConditionalOnProperty(name = "modulith.voucher.enabled", havingValue = "true")
class VoucherController {
    private final VoucherRepository vouchers;
    private final OrderOperations orders;
    private final OrderOtherOperations other;

    VoucherController(VoucherRepository vouchers, OrderOperations orders, OrderOtherOperations other) {
        this.vouchers = vouchers;
        this.orders = orders;
        this.other = other;
    }

    @PostMapping("/getVoucher") Map<String,Object> getVoucher(@RequestBody Map<String,Object> request) {
        String id = String.valueOf(request.get("orderId"));
        Map<String,Object> found = vouchers.find(id);
        if (found != null) return found;
        int type = Integer.parseInt(String.valueOf(request.get("type")));
        VoucherDetails details;
        if (type == 0) {
            var result = other.getOrderById(id);
            if (!(result.getData() instanceof trainticket.orderother.Order order))
                throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR,"Order not found");
            details = new VoucherDetails(id,millis(order.getTravelDate()),millis(order.getTravelTime()),
                    order.getContactsName(),order.getTrainNumber(),order.getSeatClass(),order.getSeatNumber(),
                    order.getFrom(),order.getTo(),Float.parseFloat(order.getPrice()));
        } else {
            var result = orders.getOrderById(id);
            if (!(result.getData() instanceof trainticket.orders.Order order))
                throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR,"Order not found");
            details = new VoucherDetails(id,millis(order.getTravelDate()),millis(order.getTravelTime()),
                    order.getContactsName(),order.getTrainNumber(),order.getSeatClass(),order.getSeatNumber(),
                    order.getFrom(),order.getTo(),Float.parseFloat(order.getPrice()));
        }
        vouchers.insert(details);
        return vouchers.find(id);
    }

    private String millis(Date date) { return date == null ? "None" : Long.toString(date.getTime()); }
}
