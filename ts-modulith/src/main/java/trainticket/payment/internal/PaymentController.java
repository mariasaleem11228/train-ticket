package trainticket.payment.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.*;
import trainticket.payment.PaymentOperations;
import trainticket.payment.PaymentRequest;

@RestController
@ConditionalOnProperty(name="modulith.payment.enabled", havingValue="true")
@RequestMapping("/api/v1/paymentservice")
class PaymentController {
    private final PaymentOperations payment;
    PaymentController(PaymentOperations payment) { this.payment=payment; }
    @GetMapping("/welcome") String welcome() { return "Welcome to [ Payment Service ] !"; }
    @PostMapping("/payment") Object pay(@RequestBody PaymentRequest request) { return payment.pay(request); }
    @PostMapping("/payment/money") Object addMoney(@RequestBody PaymentRequest request) {
        return payment.addMoney(request);
    }
    @GetMapping("/payment") Object all() { return payment.all(); }
}
