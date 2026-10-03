package trainticket.config.internal;

import com.mongodb.ConnectionString;
import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.model.ReplaceOptions;
import jakarta.annotation.PreDestroy;
import org.bson.Document;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Repository;
import org.springframework.web.server.ResponseStatusException;
import trainticket.config.Config;
import trainticket.runtime.WriteOwnership;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import static com.mongodb.client.model.Filters.eq;

@Repository
@ConditionalOnProperty(name="modulith.config.enabled", havingValue="true")
class ConfigRepository {
    private final MongoClient client;
    private final MongoCollection<Document> collection;
    private final boolean writesEnabled;
    private final WriteOwnership ownership;

    ConfigRepository(@Value("${modulith.config.mongo-uri}") String uri,
                     @Value("${modulith.config.writes-enabled:false}") boolean writesEnabled,
                     WriteOwnership ownership) {
        ConnectionString connection = new ConnectionString(uri);
        client = MongoClients.create(uri);
        collection = client.getDatabase(Objects.requireNonNull(connection.getDatabase(), "Config database required"))
                .getCollection("config");
        this.writesEnabled = writesEnabled;
        this.ownership = ownership;
    }

    Config find(String name) { return from(collection.find(eq("_id", name)).first()); }
    List<Config> all() {
        List<Config> result = new ArrayList<>();
        for (Document document : collection.find()) result.add(from(document));
        return result;
    }
    void save(Config config) {
        requireWriter();
        collection.replaceOne(eq("_id", config.getName()), new Document("_id", config.getName())
                .append("value", config.getValue()).append("description", config.getDescription())
                .append("_class", "config.entity.Config"), new ReplaceOptions().upsert(true));
    }
    void delete(String name) { requireWriter(); collection.deleteOne(eq("_id", name)); }
    private Config from(Document document) {
        return document == null ? null : new Config(document.getString("_id"),
                document.getString("value"), document.getString("description"));
    }
    private void requireWriter() {
        if (!writesEnabled || !ownership.permits("config"))
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "Config writes disabled");
    }
    @PreDestroy void close() { client.close(); }
}
