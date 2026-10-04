package trainticket.travel;

public record TravelResult<T>(int status, String msg, T data) { }
