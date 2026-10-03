package trainticket.orderother.internal;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.mongodb.client.*;
import com.mongodb.client.model.ReplaceOptions;
import org.bson.Document;
import org.bson.types.Binary;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Repository;
import org.springframework.web.server.ResponseStatusException;
import trainticket.orderother.Order;
import jakarta.annotation.PreDestroy;
import java.util.*;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import static com.mongodb.client.model.Filters.*;

/** Orders owns its separate database. Legacy UUID subtype/byte order is retained. */
@Repository
@ConditionalOnProperty(name="modulith.order-other.enabled", havingValue="true")
class OrderOtherRepository {
    @org.springframework.beans.factory.annotation.Autowired(required=false)
    private trainticket.runtime.WriteOwnership ownership;
    private final MongoClient client;
    private final MongoCollection<Document> collection;
    private final ObjectMapper mapper = new ObjectMapper();
    private final boolean writesEnabled;
    OrderOtherRepository(@Value("${modulith.order-other.mongo-uri}") String uri,
                    @Value("${modulith.order-other.writes-enabled:false}") boolean writesEnabled) {
        com.mongodb.ConnectionString connection = new com.mongodb.ConnectionString(uri);
        this.client = MongoClients.create(uri);
        this.collection = client.getDatabase(Objects.requireNonNull(connection.getDatabase(), "OrderOther database required")).getCollection("orders");
        this.writesEnabled = writesEnabled;
    }
    private Binary id(UUID value) {
        if (value == null) return null;
        byte[] bytes = ByteBuffer.allocate(16).order(ByteOrder.LITTLE_ENDIAN)
                .putLong(value.getMostSignificantBits()).putLong(value.getLeastSignificantBits()).array();
        return new Binary((byte)3, bytes);
    }
    private UUID uuid(Object value) {
        if (value == null || value instanceof UUID) return (UUID)value;
        Binary binary = (Binary)value;
        if (binary.getType() != 3) throw new IllegalArgumentException("Expected legacy UUID subtype 3");
        ByteBuffer bytes = ByteBuffer.wrap(binary.getData()).order(ByteOrder.LITTLE_ENDIAN);
        return new UUID(bytes.getLong(), bytes.getLong());
    }
    private Order from(Document document) {
        if (document == null) return null;
        Map<String,Object> values = new HashMap<>(document);
        values.put("id", uuid(values.remove("_id")));
        values.put("accountId", uuid(values.get("accountId")));
        values.remove("_class");
        return mapper.convertValue(values, Order.class);
    }
    private ArrayList<Order> read(FindIterable<Document> documents) {
        ArrayList<Order> result = new ArrayList<>();
        for (Document doc : documents) result.add(from(doc));
        return result;
    }
    Order findById(UUID value) { return from(collection.find(eq("_id", id(value))).first()); }
    ArrayList<Order> findAll() { return read(collection.find()); }
    ArrayList<Order> findByAccountId(UUID value) { return read(collection.find(eq("accountId", id(value)))); }
    ArrayList<Order> findByTravelDateAndTrainNumber(Date date, String train) {
        return read(collection.find(and(eq("travelDate", date), eq("trainNumber", train))));
    }
    private void requireWriter() {
        if (!writesEnabled || (ownership != null && !ownership.permits("orderother")))
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "OrderOther writes disabled");
    }
    @SuppressWarnings("unchecked")
    void save(Order order) {
        requireWriter();
        Document doc = new Document(mapper.convertValue(order, Map.class));
        doc.remove("id");
        doc.put("_id", id(order.getId()));
        doc.put("accountId", id(order.getAccountId()));
        doc.put("boughtDate", order.getBoughtDate());
        doc.put("travelDate", order.getTravelDate());
        doc.put("travelTime", order.getTravelTime());
        doc.put("_class", "other.entity.Order");
        collection.replaceOne(eq("_id", id(order.getId())), doc, new ReplaceOptions().upsert(true));
    }
    void deleteById(UUID value) { requireWriter(); collection.deleteOne(eq("_id", id(value))); }
    void ping() { collection.estimatedDocumentCount(); }
    @PreDestroy void close() { client.close(); }
}
