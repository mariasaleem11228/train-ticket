package trainticket.travel2;

public record TravelResult<T>(int status, String msg, T data) { }
