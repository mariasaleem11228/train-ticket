package trainticket.train;

public record TrainResult<T>(Integer status, String msg, T data) { }
