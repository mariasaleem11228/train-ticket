package trainticket.food.internal;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import trainticket.food.FoodOrder;
import trainticket.food.FoodOperations;
import trainticket.food.FoodResult;
import trainticket.foodmap.FoodMapOperations;
import trainticket.route.Route;
import trainticket.station.StationOperations;
import trainticket.travel.TravelOperations;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Service
@ConditionalOnProperty(name="modulith.food.enabled",havingValue="true")
class FoodApplicationService implements FoodOperations {
    private static final Logger LOG=LoggerFactory.getLogger(FoodApplicationService.class);
    private final FoodOrderRepository orders;
    private final FoodDeliveryPublisher delivery;
    private final FoodMapOperations catalogue;
    private final TravelOperations travel;
    private final StationOperations stations;
    FoodApplicationService(FoodOrderRepository orders,FoodDeliveryPublisher delivery,
                           FoodMapOperations catalogue,TravelOperations travel,StationOperations stations) {
        this.orders=orders;this.delivery=delivery;this.catalogue=catalogue;
        this.travel=travel;this.stations=stations;
    }
    FoodResult<?> all() {
        List<FoodOrder> rows=orders.all();
        return rows.isEmpty()?new FoodResult<>(0,"No Content",null):new FoodResult<>(1,"Success.",rows);
    }
    FoodResult<?> byOrder(UUID orderId) {
        FoodOrder row=orders.byOrder(orderId);
        return row==null?new FoodResult<>(0,"Order Id Is Non-Existent.",null):
                new FoodResult<>(1,"Success.",row);
    }
    @Override public FoodResult<?> create(FoodOrder input) {
        if (orders.byOrder(input.orderId())!=null)
            return new FoodResult<>(0,"Order Id Has Existed.",null);
        FoodOrder created=new FoodOrder(UUID.randomUUID(),input.orderId(),input.foodType(),
                input.foodType()==2?input.stationName():null,
                input.foodType()==2?input.storeName():null,input.foodName(),input.price());
        orders.save(created);
        try { delivery.publish(input); }
        catch (Exception error) { LOG.error("Food delivery publish failed for {}",input.orderId(),error); }
        return new FoodResult<>(1,"Success.",created);
    }
    FoodResult<?> update(FoodOrder input) {
        FoodOrder previous=input.id()==null?null:orders.byId(input.id());
        if (previous==null)return new FoodResult<>(0,"Order Id Is Non-Existent.",null);
        FoodOrder updated=new FoodOrder(previous.id(),previous.orderId(),input.foodType(),
                input.foodType()==1?input.stationName():previous.stationName(),
                input.foodType()==1?input.storeName():previous.storeName(),
                input.foodName(),input.price());
        orders.save(updated);
        return new FoodResult<>(1,"Success",updated);
    }
    FoodResult<?> delete(UUID orderId) {
        if (orders.byOrder(orderId)==null)return new FoodResult<>(0,"Order Id Is Non-Existent.",null);
        orders.delete(orderId);
        return new FoodResult<>(1,"Success.",null);
    }
    FoodResult<?> menu(String date,String start,String end,String tripId) {
        if (tripId==null || tripId.length()<=2)return new FoodResult<>(0,"Trip id is not suitable",null);
        List<Map<String,Object>> trainFoods=catalogue.trainFoods(tripId);
        var routeResult=travel.route(tripId);
        if (routeResult.status()!=1 || !(routeResult.data() instanceof Route route))
            return new FoodResult<>(0,"Get All Food Failed",emptyMenu());
        List<String> selected=new ArrayList<>(route.getStations());
        String startId=stationId(start);
        String endId=stationId(end);
        // Match the deployed Food service's in-place filtering, including its index skip.
        if (startId!=null)for (int i=0;i<selected.size();i++) {
            if (selected.get(i).equals(startId))break;
            selected.remove(i);
        }
        if (endId!=null)for (int i=selected.size()-1;i>=0;i--) {
            if (selected.get(i).equals(endId))break;
            selected.remove(i);
        }
        List<Map<String,Object>> stores=catalogue.stores(selected);
        if (stores.isEmpty())return new FoodResult<>(0,"Get All Food Failed",emptyMenu());
        Map<String,List<Map<String,Object>>> byStation=new LinkedHashMap<>();
        for (String station:selected) {
            List<Map<String,Object>> matching=new ArrayList<>();
            for (Map<String,Object> store:stores)if (station.equals(store.get("stationId")))matching.add(store);
            byStation.put(station,matching);
        }
        Map<String,Object> result=new LinkedHashMap<>();
        result.put("trainFoodList",trainFoods);result.put("foodStoreListMap",byStation);
        return new FoodResult<>(1,"Get All Food Success",result);
    }
    private String stationId(String name) {
        if (name==null || name.isBlank())return null;
        Object value=stations.idForName(name).getData();
        return value==null?null:value.toString();
    }
    private Map<String,Object> emptyMenu() {
        Map<String,Object> value=new LinkedHashMap<>();
        value.put("trainFoodList",null);value.put("foodStoreListMap",null);return value;
    }
}
