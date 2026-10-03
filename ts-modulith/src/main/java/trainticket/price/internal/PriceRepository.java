package trainticket.price.internal;

import com.mongodb.ConnectionString;
import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.model.ReplaceOptions;
import jakarta.annotation.PreDestroy;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.UUID;
import org.bson.Document;
import org.bson.types.Binary;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Repository;
import org.springframework.web.server.ResponseStatusException;
import trainticket.price.PriceConfig;
import trainticket.runtime.WriteOwnership;
import static com.mongodb.client.model.Filters.eq;

/** Preserves the deployed Java-legacy UUID subtype 3 and original collection. */
@Repository
@ConditionalOnProperty(name="modulith.price.enabled",havingValue="true")
class PriceRepository {
    private final MongoClient client;
    private final MongoCollection<Document> collection;
    private final boolean writesEnabled;
    private final WriteOwnership ownership;
    PriceRepository(@Value("${modulith.price.mongo-uri}") String uri,
                    @Value("${modulith.price.writes-enabled:false}") boolean writesEnabled,
                    WriteOwnership ownership) {
        ConnectionString connection=new ConnectionString(uri);
        client=MongoClients.create(uri);
        collection=client.getDatabase(Objects.requireNonNull(connection.getDatabase(),"Price database required"))
                .getCollection("price_config");
        this.writesEnabled=writesEnabled;this.ownership=ownership;
    }
    private Binary id(UUID value) {
        byte[] bytes=ByteBuffer.allocate(16).order(ByteOrder.LITTLE_ENDIAN)
                .putLong(value.getMostSignificantBits()).putLong(value.getLeastSignificantBits()).array();
        return new Binary((byte)3,bytes);
    }
    private UUID uuid(Object value) {
        ByteBuffer bytes=ByteBuffer.wrap(((Binary)value).getData()).order(ByteOrder.LITTLE_ENDIAN);
        return new UUID(bytes.getLong(),bytes.getLong());
    }
    private PriceConfig from(Document doc) {
        return doc==null ? null : new PriceConfig(uuid(doc.get("_id")),doc.getString("trainType"),
                doc.getString("routeId"),((Number)doc.getOrDefault("basicPriceRate",0)).doubleValue(),
                ((Number)doc.getOrDefault("firstClassPriceRate",0)).doubleValue());
    }
    PriceConfig find(UUID value) { return value==null ? null : from(collection.find(eq("_id",id(value))).first()); }
    PriceConfig find(String routeId,String trainType) {
        return from(collection.find(new Document("routeId",routeId).append("trainType",trainType)).first());
    }
    List<PriceConfig> all() {
        List<PriceConfig> result=new ArrayList<>();
        for (Document doc:collection.find()) result.add(from(doc));
        return result;
    }
    void save(PriceConfig config) {
        requireWriter();
        Binary key=id(config.getId());
        collection.replaceOne(eq("_id",key),new Document("_id",key)
                .append("trainType",config.getTrainType()).append("routeId",config.getRouteId())
                .append("basicPriceRate",config.getBasicPriceRate())
                .append("firstClassPriceRate",config.getFirstClassPriceRate())
                .append("_class","price.entity.PriceConfig"),new ReplaceOptions().upsert(true));
    }
    void delete(UUID value) { requireWriter();collection.deleteOne(eq("_id",id(value))); }
    private void requireWriter() {
        if (!writesEnabled || !ownership.permits("price"))
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,"Price writes disabled");
    }
    @PreDestroy void close() {client.close();}
}
