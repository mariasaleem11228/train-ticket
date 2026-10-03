package trainticket.foodmap.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import trainticket.foodmap.FoodMapOperations;

import java.util.List;
import java.util.Map;

@Service
@ConditionalOnProperty(name="modulith.foodmap.enabled",havingValue="true")
class FoodMapApplicationService implements FoodMapOperations {
    private final FoodMapRepository repository;
    FoodMapApplicationService(FoodMapRepository repository) { this.repository=repository; }
    public List<Map<String,Object>> trainFoods(String tripId) { return repository.trains(tripId); }
    public List<Map<String,Object>> stores(List<String> stationIds) { return repository.stores(stationIds); }
    public Map<String,Object> store(String storeId) { return repository.store(storeId); }
}
