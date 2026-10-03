package trainticket.insidepayment.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.*;
import trainticket.insidepayment.*;

@RestController
@RequestMapping("/api/v1/inside_pay_service")
@ConditionalOnProperty(name="modulith.inside-payment.enabled",havingValue="true")
class InsidePaymentController {
    private final InsidePaymentOperations service;
    InsidePaymentController(InsidePaymentOperations service) { this.service=service; }

    @GetMapping("/welcome") String welcome() { return "Welcome to [ InsidePayment Service ] !"; }
    @PostMapping("/inside_payment") InsidePaymentResult<?> pay(@RequestBody InsidePaymentRequest request) { return service.pay(request); }
    @PostMapping("/inside_payment/account") InsidePaymentResult<?> createAccount(@RequestBody AccountRequest request) { return service.createAccount(request); }
    @GetMapping("/inside_payment/{userId}/{money}") InsidePaymentResult<?> addMoney(@PathVariable String userId,@PathVariable String money) { return service.addMoney(userId,money); }
    @GetMapping("/inside_payment/payment") InsidePaymentResult<?> queryPayment() { return service.queryPayment(); }
    @GetMapping("/inside_payment/account") InsidePaymentResult<?> queryAccount() { return service.queryAccount(); }
    @GetMapping("/inside_payment/drawback/{userId}/{money}") InsidePaymentResult<?> drawBack(@PathVariable String userId,@PathVariable String money) { return service.drawBack(userId,money); }
    @PostMapping("/inside_payment/difference") InsidePaymentResult<?> payDifference(@RequestBody InsidePaymentRequest request) { return service.payDifference(request); }
    @GetMapping("/inside_payment/money") InsidePaymentResult<?> queryAddMoney() { return service.queryAddMoney(); }
}
