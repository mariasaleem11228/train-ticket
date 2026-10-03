package trainticket.route;

public record RouteResult<T>(Integer status, String msg, T data) { }
