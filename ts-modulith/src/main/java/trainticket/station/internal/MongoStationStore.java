package trainticket.station.internal;

import com.mongodb.client.MongoCollection;
import com.mongodb.client.model.ReplaceOptions;
import org.bson.Document;
import org.bson.types.ObjectId;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.stereotype.Repository;
import trainticket.station.Station;
import java.util.ArrayList;
import java.util.List;
import static com.mongodb.client.model.Filters.eq;

/** Explicit mapping keeps the legacy collection, string IDs and class marker intact. */
@Repository
class MongoStationStore implements StationStore {
    private final MongoTemplate mongo;
    MongoStationStore(MongoTemplate mongo) { this.mongo = mongo; }
    private MongoCollection<Document> collection() { return mongo.getCollection("station"); }
    private Station from(Document doc) {
        return doc == null ? null : new Station(doc.get("_id").toString(), doc.getString("name"),
                ((Number) doc.getOrDefault("stayTime", 0)).intValue());
    }
    private Object mongoId(String id) {
        // Legacy Spring Data @Id converts valid 24-character hex strings to ObjectId.
        return id != null && ObjectId.isValid(id) ? new ObjectId(id) : id;
    }
    public Station findById(String id) { return from(collection().find(eq("_id", mongoId(id))).first()); }
    public Station findByName(String name) { return from(collection().find(eq("name", name)).first()); }
    public List<Station> findAll() {
        List<Station> result = new ArrayList<>();
        for (Document doc : collection().find()) { result.add(from(doc)); }
        return result;
    }
    public void save(Station station) {
        Document doc = new Document("_id", mongoId(station.getId())).append("name", station.getName())
                .append("stayTime", station.getStayTime()).append("_class", "fdse.microservice.entity.Station");
        collection().replaceOne(eq("_id", mongoId(station.getId())), doc, new ReplaceOptions().upsert(true));
    }
    public void delete(String id) { collection().deleteOne(eq("_id", mongoId(id))); }
}
