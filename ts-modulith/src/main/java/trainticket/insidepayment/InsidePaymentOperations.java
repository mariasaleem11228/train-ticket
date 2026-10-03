package trainticket.insidepayment;

public interface InsidePaymentOperations {
    InsidePaymentResult<?> pay(InsidePaymentRequest request);
    InsidePaymentResult<?> createAccount(AccountRequest request);
    InsidePaymentResult<?> addMoney(String userId, String money);
    InsidePaymentResult<?> queryAccount();
    InsidePaymentResult<?> queryPayment();
    InsidePaymentResult<?> drawBack(String userId, String money);
    InsidePaymentResult<?> payDifference(InsidePaymentRequest request);
    InsidePaymentResult<?> queryAddMoney();
}
