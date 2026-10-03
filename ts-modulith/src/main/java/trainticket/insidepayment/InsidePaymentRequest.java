package trainticket.insidepayment;

public record InsidePaymentRequest(String userId, String orderId, String tripId, String price) {}
