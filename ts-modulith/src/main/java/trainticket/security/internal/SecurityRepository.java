package trainticket.security.internal;

import com.mongodb.ConnectionString;
import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.model.ReplaceOptions;
import jakarta.annotation.PreDestroy;
import org.bson.Document;
import org.bson.types.Binary;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Repository;
import org.springframework.web.server.ResponseStatusException;
import trainticket.runtime.WriteOwnership;
import trainticket.security.SecurityConfig;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.UUID;
import static com.mongodb.client.model.Filters.eq;

/** Owns the original Security MongoDB; preserves Java-legacy UUID subtype 3. */
@Repository
@ConditionalOnProperty(name="modulith.security.enabled", havingValue="true")
class SecurityRepository {
    private final MongoClient client;
    private final MongoCollection<Document> collection;
    private final boolean writesEnabled;
    private final WriteOwnership ownership;

    SecurityRepository(@Value("${modulith.security.mongo-uri}") String uri,
                       @Value("${modulith.security.writes-enabled:false}") boolean writesEnabled,
                       WriteOwnership ownership) {
        ConnectionString connection = new ConnectionString(uri);
        client = MongoClients.create(uri);
        collection = client.getDatabase(Objects.requireNonNull(connection.getDatabase(), "Security database required"))
                .getCollection("security_config");
        this.writesEnabled = writesEnabled;
        this.ownership = ownership;
    }
    private Binary id(UUID value) {
        byte[] bytes = ByteBuffer.allocate(16).order(ByteOrder.LITTLE_ENDIAN)
                .putLong(value.getMostSignificantBits()).putLong(value.getLeastSignificantBits()).array();
        return new Binary((byte)3, bytes);
    }
    private UUID uuid(Object value) {
        Binary binary = (Binary)value;
        ByteBuffer bytes = ByteBuffer.wrap(binary.getData()).order(ByteOrder.LITTLE_ENDIAN);
        return new UUID(bytes.getLong(), bytes.getLong());
    }
    private SecurityConfig from(Document doc) {
        if (doc == null) return null;
        SecurityConfig result = new SecurityConfig();
        result.setId(uuid(doc.get("_id")));
        result.setName(doc.getString("name"));
        result.setValue(doc.getString("value"));
        result.setDescription(doc.getString("description"));
        return result;
    }
    List<SecurityConfig> all() {
        List<SecurityConfig> result = new ArrayList<>();
        for (Document doc : collection.find()) result.add(from(doc));
        return result;
    }
    SecurityConfig findByName(String name) { return from(collection.find(eq("name", name)).first()); }
    SecurityConfig findById(UUID value) { return from(collection.find(eq("_id", id(value))).first()); }
    void save(SecurityConfig config) {
        requireWriter();
        collection.replaceOne(eq("_id", id(config.getId())),
                new Document("_id", id(config.getId())).append("name", config.getName())
                .append("value", config.getValue()).append("description", config.getDescription())
                .append("_class", "security.entity.SecurityConfig"), new ReplaceOptions().upsert(true));
    }
    void delete(UUID value) { requireWriter(); collection.deleteOne(eq("_id", id(value))); }
    private void requireWriter() {
        if (!writesEnabled || !ownership.permits("security"))
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "Security writes disabled");
    }
    @PreDestroy void close() { client.close(); }
}
