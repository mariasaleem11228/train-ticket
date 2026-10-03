package trainticket.payment;

import java.util.List;

public interface PaymentOperations {
    PaymentResult<?> pay(PaymentRequest request);
    PaymentResult<?> addMoney(PaymentRequest request);
    PaymentResult<List<PaymentRecord>> all();
}
