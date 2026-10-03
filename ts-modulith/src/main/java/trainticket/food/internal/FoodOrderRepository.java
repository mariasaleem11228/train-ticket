package trainticket.food.internal;

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
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Repository;
import org.springframework.web.server.ResponseStatusException;
import trainticket.food.FoodOrder;
import trainticket.runtime.WriteOwnership;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.UUID;

import static com.mongodb.client.model.Filters.eq;

@Repository
@ConditionalOnProperty(name="modulith.food.enabled",havingValue="true")
class FoodOrderRepository {
    private final MongoClient client;
    private final MongoCollection<Document> collection;
    private final boolean writesEnabled;
    private final WriteOwnership ownership;

    FoodOrderRepository(@Value("${modulith.food.mongo-uri}") String uri,
                        @Value("${modulith.food.writes-enabled:false}") boolean writesEnabled,
                        WriteOwnership ownership) {
        ConnectionString connection=new ConnectionString(uri);
        client=MongoClients.create(MongoClientSettings.builder().applyConnectionString(connection)
                .uuidRepresentation(UuidRepresentation.JAVA_LEGACY).build());
        collection=client.getDatabase(Objects.requireNonNull(connection.getDatabase(),"Food database required"))
                .getCollection("foodorder");
        this.writesEnabled=writesEnabled;this.ownership=ownership;
    }
    FoodOrder byId(UUID id) { return from(collection.find(eq("_id",id)).first()); }
    FoodOrder byOrder(UUID orderId) { return from(collection.find(eq("orderId",orderId)).first()); }
    List<FoodOrder> all() {
        List<FoodOrder> result=new ArrayList<>();
        for (Document row:collection.find()) result.add(from(row));
        return result;
    }
    void save(FoodOrder order) {
        guard();
        Document row=new Document("_id",order.id()).append("_class","foodsearch.entity.FoodOrder")
                .append("orderId",order.orderId()).append("foodType",order.foodType())
                .append("stationName",order.stationName()).append("storeName",order.storeName())
                .append("foodName",order.foodName()).append("price",order.price());
        collection.replaceOne(eq("_id",order.id()),row,new com.mongodb.client.model.ReplaceOptions().upsert(true));
    }
    void delete(UUID orderId) { guard();collection.deleteMany(eq("orderId",orderId)); }
    private void guard() {
        if (!writesEnabled || !ownership.permits("food"))
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,"Food writes disabled");
    }
    private FoodOrder from(Document row) {
        return row==null?null:new FoodOrder(row.get("_id",UUID.class),row.get("orderId",UUID.class),
                row.getInteger("foodType"),row.getString("stationName"),row.getString("storeName"),
                row.getString("foodName"),((Number)row.get("price")).doubleValue());
    }
    @PreDestroy void close() { client.close(); }
}
