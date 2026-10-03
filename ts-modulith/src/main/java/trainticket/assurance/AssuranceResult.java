package trainticket.assurance;

public record AssuranceResult<T>(int status, String msg, T data) { }
