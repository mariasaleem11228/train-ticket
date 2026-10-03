package trainticket.food;

import java.util.UUID;

/** Deployed Food service JSON and Mongo contract. */
public record FoodOrder(UUID id,UUID orderId,int foodType,String stationName,
                        String storeName,String foodName,double price) { }
