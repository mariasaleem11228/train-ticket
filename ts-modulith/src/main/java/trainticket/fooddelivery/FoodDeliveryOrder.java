package trainticket.fooddelivery;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.util.List;
import java.util.Map;

@JsonIgnoreProperties(ignoreUnknown = true)
public record FoodDeliveryOrder(String id, String stationFoodStoreId,
                                List<Map<String,Object>> foodList, String tripId,
                                int seatNo, String createdTime, String deliveryTime,
                                double deliveryFee) {
    public FoodDeliveryOrder withIdAndFee(String id, double fee) {
        return new FoodDeliveryOrder(id, stationFoodStoreId, foodList, tripId,
                seatNo, createdTime, deliveryTime, fee);
    }
    public FoodDeliveryOrder withTripId(String value) {
        return new FoodDeliveryOrder(id, stationFoodStoreId, foodList, value,
                seatNo, createdTime, deliveryTime, deliveryFee);
    }
    public FoodDeliveryOrder withSeatNo(int value) {
        return new FoodDeliveryOrder(id, stationFoodStoreId, foodList, tripId,
                value, createdTime, deliveryTime, deliveryFee);
    }
    public FoodDeliveryOrder withDeliveryTime(String value) {
        return new FoodDeliveryOrder(id, stationFoodStoreId, foodList, tripId,
                seatNo, createdTime, value, deliveryFee);
    }
}
