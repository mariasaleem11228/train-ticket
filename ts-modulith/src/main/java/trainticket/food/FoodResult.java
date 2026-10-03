package trainticket.food;

public record FoodResult<T>(int status,String msg,T data) { }
