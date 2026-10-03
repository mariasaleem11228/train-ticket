package trainticket.rebook;

public record RebookResult<T>(int status,String msg,T data) { }
