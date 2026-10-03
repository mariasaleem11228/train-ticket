package trainticket.foodmap.internal;

import com.mongodb.ConnectionString;
import com.mongodb.MongoClientSettings;
import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;
import com.mongodb.client.MongoCollection;
import jakarta.annotation.PreDestroy;
import org.bson.Document;
import org.bson.UuidRepresentation;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Repository;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

import static com.mongodb.client.model.Filters.eq;
import static com.mongodb.client.model.Filters.in;

@Repository
@ConditionalOnProperty(name="modulith.foodmap.enabled",havingValue="true")
class FoodMapRepository {
    private final MongoClient client;
    private final MongoCollection<Document> trains;
    private final MongoCollection<Document> stores;

    FoodMapRepository(@Value("${modulith.foodmap.mongo-uri}") String uri) {
        ConnectionString connection=new ConnectionString(uri);
        client=MongoClients.create(MongoClientSettings.builder().applyConnectionString(connection)
                .uuidRepresentation(UuidRepresentation.JAVA_LEGACY).build());
        var database=client.getDatabase(Objects.requireNonNull(connection.getDatabase(),"Food Map database required"));
        trains=database.getCollection("trainfoods");
        stores=database.getCollection("stores");
    }

    List<Map<String,Object>> trains() { return rows(trains.find(),true); }
    List<Map<String,Object>> trains(String tripId) { return rows(trains.find(eq("tripId",tripId)),true); }
    List<Map<String,Object>> stores() { return rows(stores.find(),false); }
    List<Map<String,Object>> stores(String stationId) { return rows(stores.find(eq("stationId",stationId)),false); }
    List<Map<String,Object>> stores(List<String> stationIds) {
        return stationIds.isEmpty()?List.of():rows(stores.find(in("stationId",stationIds)),false);
    }
    Map<String,Object> store(String storeId) {
        if (storeId==null)return null;
        try {
            List<Map<String,Object>> result=rows(stores.find(eq("_id",java.util.UUID.fromString(storeId))).limit(1),false);
            return result.isEmpty()?null:result.get(0);
        } catch (IllegalArgumentException invalid) {
            return null;
        }
    }

    private List<Map<String,Object>> rows(Iterable<Document> source,boolean train) {
        List<Map<String,Object>> result=new ArrayList<>();
        for (Document row:source) {
            Map<String,Object> value=new LinkedHashMap<>();
            value.put("id",row.get("_id",java.util.UUID.class));
            if (train) value.put("tripId",row.getString("tripId"));
            else {
                value.put("stationId",row.getString("stationId"));
                value.put("storeName",row.getString("storeName"));
                value.put("telephone",row.getString("telephone"));
                value.put("businessTime",row.getString("businessTime"));
                value.put("deliveryFee",((Number)row.get("deliveryFee")).doubleValue());
            }
            List<Map<String,Object>> food=new ArrayList<>();
            for (Document item:row.getList("foodList",Document.class)) {
                food.add(Map.of("foodName",item.getString("foodName"),
                        "price",((Number)item.get("price")).doubleValue()));
            }
            value.put("foodList",food);
            result.add(value);
        }
        return result;
    }

    @PreDestroy void close() { client.close(); }
}
