package trainticket.consign;

public record ConsignResult<T>(int status, String msg, T data) { }
