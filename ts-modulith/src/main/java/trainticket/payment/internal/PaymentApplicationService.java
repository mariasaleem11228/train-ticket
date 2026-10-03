package trainticket.payment.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import trainticket.payment.*;
import java.util.List;
import java.util.UUID;

/** Preserves the deployed payment record and duplicate-order responses. */
@Service
@ConditionalOnProperty(name="modulith.payment.enabled", havingValue="true")
class PaymentApplicationService implements PaymentOperations {
    private final PaymentRepository repository;
    PaymentApplicationService(PaymentRepository repository) { this.repository=repository; }

    @Override public PaymentResult<?> pay(PaymentRequest request) {
        if(repository.byOrderId(request.orderId())!=null)
            return new PaymentResult<>(0,"Pay Failed, order not found with order id"+request.orderId(),null);
        repository.insert(new PaymentRecord(UUID.randomUUID().toString(),request.orderId(),
                request.userId(),request.price()));
        return new PaymentResult<>(1,"Pay Success",null);
    }
    @Override public PaymentResult<?> addMoney(PaymentRequest request) {
        MoneyRecord money=new MoneyRecord(request.userId(),request.price());
        repository.addMoney(money);
        return new PaymentResult<>(1,"Add Money Success",money);
    }
    @Override public PaymentResult<List<PaymentRecord>> all() {
        List<PaymentRecord> records=repository.all();
        return records.isEmpty()?new PaymentResult<>(0,"No Content",null)
                :new PaymentResult<>(1,"Query Success",records);
    }
}
