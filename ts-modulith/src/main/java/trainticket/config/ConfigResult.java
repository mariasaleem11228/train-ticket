package trainticket.config;

public record ConfigResult<T>(Integer status, String msg, T data) { }
