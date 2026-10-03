package trainticket.assurance.internal;

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
import trainticket.assurance.AssuranceRecord;
import trainticket.runtime.WriteOwnership;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.UUID;

import static com.mongodb.client.model.Filters.eq;

@Repository
@ConditionalOnProperty(name="modulith.assurance.enabled", havingValue="true")
class AssuranceRepository {
    private final MongoClient client;
    private final MongoCollection<Document> collection;
    private final boolean writesEnabled;
    private final WriteOwnership ownership;

    AssuranceRepository(@Value("${modulith.assurance.mongo-uri}") String uri,
                        @Value("${modulith.assurance.writes-enabled:false}") boolean writesEnabled,
                        WriteOwnership ownership) {
        ConnectionString connection = new ConnectionString(uri);
        client = MongoClients.create(MongoClientSettings.builder().applyConnectionString(connection)
                .uuidRepresentation(UuidRepresentation.JAVA_LEGACY).build());
        collection = client.getDatabase(Objects.requireNonNull(connection.getDatabase(), "Assurance database required"))
                .getCollection("assurance");
        this.writesEnabled = writesEnabled;
        this.ownership = ownership;
    }

    AssuranceRecord byId(UUID id) { return from(collection.find(eq("_id", id)).first()); }
    AssuranceRecord byOrder(UUID orderId) { return from(collection.find(eq("orderId", orderId)).first()); }
    List<AssuranceRecord> all() {
        List<AssuranceRecord> records = new ArrayList<>();
        for (Document row : collection.find()) records.add(from(row));
        return records;
    }
    void save(AssuranceRecord record) {
        requireWriter();
        Document row = new Document("_id", record.id()).append("_class", "assurance.entity.Assurance")
                .append("orderId", record.orderId()).append("type", record.type());
        collection.replaceOne(eq("_id", record.id()), row, new ReplaceOptions().upsert(true));
    }
    void deleteById(UUID id) { requireWriter(); collection.deleteOne(eq("_id", id)); }
    void deleteByOrder(UUID orderId) { requireWriter(); collection.deleteMany(eq("orderId", orderId)); }
    private AssuranceRecord from(Document row) {
        return row == null ? null : new AssuranceRecord(row.get("_id", UUID.class),
                row.get("orderId", UUID.class), row.getString("type"));
    }
    private void requireWriter() {
        if (!writesEnabled || !ownership.permits("assurance"))
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "Assurance writes disabled");
    }
    @PreDestroy void close() { client.close(); }
}
