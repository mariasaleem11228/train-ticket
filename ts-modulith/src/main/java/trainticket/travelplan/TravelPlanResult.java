package trainticket.travelplan;

public record TravelPlanResult<T>(int status, String msg, T data) { }
