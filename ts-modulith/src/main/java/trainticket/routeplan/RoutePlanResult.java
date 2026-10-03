package trainticket.routeplan;

public record RoutePlanResult<T>(int status, String msg, T data) { }
