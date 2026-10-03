package trainticket.seat;

public record SeatResult<T>(Integer status, String msg, T data) { }
