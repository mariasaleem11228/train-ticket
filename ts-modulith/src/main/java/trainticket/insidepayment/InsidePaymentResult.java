package trainticket.insidepayment;

public record InsidePaymentResult<T>(int status, String msg, T data) {}
