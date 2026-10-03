package trainticket.fooddelivery.internal;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;
import trainticket.fooddelivery.FoodDeliveryOrder;
import trainticket.foodmap.FoodMapOperations;
import trainticket.runtime.WriteOwnership;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.function.UnaryOperator;

@Service
@ConditionalOnProperty(name="modulith.fooddelivery.enabled",havingValue="true")
class FoodDeliveryApplicationService {
    record Result(int status,String msg,Object data) {}
    private final FoodDeliveryRepository repository;
    private final FoodMapOperations catalogue;
    private final WriteOwnership ownership;
    private final boolean writesEnabled;

    FoodDeliveryApplicationService(FoodDeliveryRepository repository,FoodMapOperations catalogue,
                                   WriteOwnership ownership,
                                   @Value("${modulith.fooddelivery.writes-enabled:false}") boolean writesEnabled) {
        this.repository=repository;this.catalogue=catalogue;
        this.ownership=ownership;this.writesEnabled=writesEnabled;
    }

    private void requireWrite() {
        if (!writesEnabled || !ownership.permits("fooddelivery"))
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,"Food Delivery writes disabled");
    }

    Result create(FoodDeliveryOrder input) {
        requireWrite();
        Map<String,Object> store=catalogue.store(input.stationFoodStoreId());
        if (store==null)return new Result(0,"Food store not found",null);
        Map<String,Double> prices=new HashMap<>();
        for (Map<String,Object> food:(List<Map<String,Object>>)store.get("foodList"))
            prices.put(String.valueOf(food.get("foodName")),((Number)food.get("price")).doubleValue());
        double fee=((Number)store.get("deliveryFee")).doubleValue();
        if (input.foodList()!=null)for (Map<String,Object> food:input.foodList()) {
            Double price=prices.get(String.valueOf(food.get("foodName")));
            if (price==null)return new Result(0,"Food not in store",null);
            fee+=price;
        }
        FoodDeliveryOrder saved=input.withIdAndFee(
                input.id()==null || input.id().isBlank()?UUID.randomUUID().toString():input.id(),fee);
        repository.save(saved);
        return new Result(1,"Save success",saved);
    }

    Result byId(String id) {
        FoodDeliveryOrder row=repository.byId(id);
        return row==null?new Result(0,"No such food delivery order id",id):
                new Result(1,"Get success",row);
    }
    Result all() { return new Result(1,"Get success",repository.all()); }
    Result byStore(String storeId) { return new Result(1,"Get success",repository.byStore(storeId)); }

    Result delete(String id) {
        requireWrite();
        if (repository.byId(id)==null)return new Result(0,"No such food delivery order id",id);
        repository.delete(id);
        return new Result(1,"Delete success",null);
    }

    Result update(String id,UnaryOperator<FoodDeliveryOrder> change,String message) {
        requireWrite();
        FoodDeliveryOrder old=repository.byId(id);
        if (old==null)return new Result(0,"No such delivery order id",id);
        FoodDeliveryOrder updated=change.apply(old);
        repository.save(updated);
        return new Result(1,message,updated);
    }
}
