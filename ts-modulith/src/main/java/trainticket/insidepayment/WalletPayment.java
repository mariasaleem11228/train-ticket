package trainticket.insidepayment;

public record WalletPayment(String id, String orderId, String userId, String price, String type) {}
