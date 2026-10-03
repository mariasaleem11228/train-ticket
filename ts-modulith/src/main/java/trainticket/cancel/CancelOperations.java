package trainticket.cancel;

public interface CancelOperations {
    CancelResult<?> refund(String orderId);
    CancelResult<?> cancel(String orderId,String loginId,String authorization);
}
