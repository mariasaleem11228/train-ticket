package trainticket.payment;

public record PaymentRequest(String id, String orderId, String userId, String price) { }
