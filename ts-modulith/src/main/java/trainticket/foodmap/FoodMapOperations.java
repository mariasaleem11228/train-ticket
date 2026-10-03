package trainticket.foodmap;

import java.util.List;
import java.util.Map;

/** Published catalogue contract for food booking. */
public interface FoodMapOperations {
    List<Map<String,Object>> trainFoods(String tripId);
    List<Map<String,Object>> stores(List<String> stationIds);
    Map<String,Object> store(String storeId);
}
