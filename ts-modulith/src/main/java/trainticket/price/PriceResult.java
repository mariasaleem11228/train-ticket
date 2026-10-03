package trainticket.price;

public record PriceResult<T>(Integer status,String msg,T data) { }
