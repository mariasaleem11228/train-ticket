package trainticket.security;

public record SecurityResult<T>(Integer status, String msg, T data) { }
