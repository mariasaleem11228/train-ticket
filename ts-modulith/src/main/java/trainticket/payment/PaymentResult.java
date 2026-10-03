package trainticket.payment;

public record PaymentResult<T>(int status, String msg, T data) { }
