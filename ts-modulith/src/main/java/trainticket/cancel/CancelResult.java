package trainticket.cancel;

public record CancelResult<T>(int status,String msg,T data) {}
