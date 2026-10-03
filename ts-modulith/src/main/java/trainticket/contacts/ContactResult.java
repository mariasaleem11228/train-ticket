package trainticket.contacts;

public record ContactResult<T>(Integer status, String msg, T data) { }
