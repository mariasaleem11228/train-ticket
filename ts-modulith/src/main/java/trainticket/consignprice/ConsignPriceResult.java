package trainticket.consignprice;

public record ConsignPriceResult<T>(int status, String msg, T data) { }
