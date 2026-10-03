package trainticket.train.internal;

import com.mongodb.ConnectionString;
import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.model.ReplaceOptions;
import jakarta.annotation.PreDestroy;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.bson.Document;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Repository;
import org.springframework.web.server.ResponseStatusException;
import trainticket.runtime.WriteOwnership;
import trainticket.train.TrainType;
import static com.mongodb.client.model.Filters.eq;

/** Reads the original trainType collection without reseeding it on startup. */
@Repository
@ConditionalOnProperty(name="modulith.train.enabled", havingValue="true")
class TrainRepository {
    private final MongoClient client;
    private final MongoCollection<Document> collection;
    private final boolean writesEnabled;
    private final WriteOwnership ownership;
    TrainRepository(@Value("${modulith.train.mongo-uri}") String uri,
                    @Value("${modulith.train.writes-enabled:false}") boolean writesEnabled,
                    WriteOwnership ownership) {
        ConnectionString connection = new ConnectionString(uri);
        client = MongoClients.create(uri);
        collection = client.getDatabase(Objects.requireNonNull(connection.getDatabase(), "Train database required"))
                .getCollection("trainType");
        this.writesEnabled = writesEnabled;
        this.ownership = ownership;
    }
    TrainType find(String id) { return from(collection.find(eq("_id", id)).first()); }
    List<TrainType> all() {
        List<TrainType> result = new ArrayList<>();
        for (Document doc : collection.find()) result.add(from(doc));
        return result;
    }
    void save(TrainType train) {
        requireWriter();
        String id = train.getId();
        collection.replaceOne(eq("_id", id), new Document("_id", id)
                .append("economyClass", train.getEconomyClass())
                .append("confortClass", train.getConfortClass())
                .append("averageSpeed", train.getAverageSpeed())
                .append("_class", "train.entity.TrainType"), new ReplaceOptions().upsert(true));
    }
    void delete(String id) { requireWriter(); collection.deleteOne(eq("_id", id)); }
    private TrainType from(Document doc) {
        if (doc == null) return null;
        return new TrainType(doc.getString("_id"), doc.getInteger("economyClass", 0),
                doc.getInteger("confortClass", 0), doc.getInteger("averageSpeed", 0));
    }
    private void requireWriter() {
        if (!writesEnabled || !ownership.permits("train"))
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "Train writes disabled");
    }
    @PreDestroy void close() { client.close(); }
}
