package trainticket.consignprice.internal;

import com.mongodb.ConnectionString;
import com.mongodb.MongoClientSettings;
import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.model.ReplaceOptions;
import jakarta.annotation.PreDestroy;
import org.bson.Document;
import org.bson.UuidRepresentation;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Repository;
import org.springframework.web.server.ResponseStatusException;
import trainticket.consignprice.ConsignPrice;
import trainticket.runtime.WriteOwnership;

import java.util.Objects;
import java.util.UUID;

import static com.mongodb.client.model.Filters.eq;

@Repository
@ConditionalOnProperty(name="modulith.consign-price.enabled", havingValue="true")
class ConsignPriceRepository {
    private final MongoClient client;
    private final MongoCollection<Document> collection;
    private final boolean writesEnabled;
    private final WriteOwnership ownership;
    ConsignPriceRepository(@Value("${modulith.consign-price.mongo-uri}") String uri,
                           @Value("${modulith.consign-price.writes-enabled:false}") boolean writesEnabled,
                           WriteOwnership ownership) {
        ConnectionString connection=new ConnectionString(uri);
        client=MongoClients.create(MongoClientSettings.builder().applyConnectionString(connection)
                .uuidRepresentation(UuidRepresentation.JAVA_LEGACY).build());
        collection=client.getDatabase(Objects.requireNonNull(connection.getDatabase(),"ConsignPrice database required"))
                .getCollection("consign_price");
        this.writesEnabled=writesEnabled;
        this.ownership=ownership;
    }
    ConsignPrice current() {
        Document row=collection.find(eq("index",0)).first();
        return row==null ? null : new ConsignPrice(row.get("_id",UUID.class),row.getInteger("index",0),
                row.getDouble("initialWeight"),row.getDouble("initialPrice"),
                row.getDouble("withinPrice"),row.getDouble("beyondPrice"));
    }
    void save(ConsignPrice config) {
        if (!writesEnabled || !ownership.permits("consignprice"))
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,"ConsignPrice writes disabled");
        Document row=new Document("_id",config.id()).append("_class","consignprice.entity.ConsignPrice")
                .append("index",0).append("initialWeight",config.initialWeight())
                .append("initialPrice",config.initialPrice()).append("withinPrice",config.withinPrice())
                .append("beyondPrice",config.beyondPrice());
        collection.replaceOne(eq("_id",config.id()),row,new ReplaceOptions().upsert(true));
    }
    @PreDestroy void close() { client.close(); }
}
