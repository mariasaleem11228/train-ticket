package trainticket.travel.internal;

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
import trainticket.travel.Trip;
import trainticket.travel.TripId;
import static com.mongodb.client.model.Filters.eq;

/** Mongo adapter retaining the deployed composite _id and trip collection. */
@Repository
@ConditionalOnProperty(name="modulith.travel.enabled",havingValue="true")
class TripRepository {
    private final MongoClient client;
    private final MongoCollection<Document> collection;
    private final boolean writesEnabled;
    private final WriteOwnership ownership;

    TripRepository(@Value("${modulith.travel.mongo-uri}") String uri,
                   @Value("${modulith.travel.writes-enabled:false}") boolean writesEnabled,
                   WriteOwnership ownership) {
        ConnectionString connection = new ConnectionString(uri);
        client = MongoClients.create(uri);
        collection = client.getDatabase(Objects.requireNonNull(connection.getDatabase(), "Travel database required"))
                .getCollection("trip");
        this.writesEnabled = writesEnabled;
        this.ownership = ownership;
    }

    private Document key(TripId id) { return new Document("type", id.type()).append("number", id.number()); }
    private Trip from(Document doc) {
        if (doc == null) return null;
        Document id = doc.get("_id", Document.class);
        return new Trip(new TripId(id.getString("type"), id.getString("number")),
                doc.getString("trainTypeId"), doc.getString("routeId"), doc.getDate("startingTime"),
                doc.getString("startingStationId"), doc.getString("stationsId"),
                doc.getString("terminalStationId"), doc.getDate("endTime"));
    }
    Trip find(TripId id) { return from(collection.find(eq("_id", key(id))).first()); }
    List<Trip> all() {
        List<Trip> result = new ArrayList<>();
        for (Document doc : collection.find()) result.add(from(doc));
        return result;
    }
    List<Trip> byRoute(String routeId) {
        List<Trip> result = new ArrayList<>();
        for (Document doc : collection.find(eq("routeId", routeId))) result.add(from(doc));
        return result;
    }
    void save(Trip trip) {
        requireWriter();
        Document id = key(trip.tripId());
        Document doc = new Document("_id", id).append("_class", "travel.entity.Trip")
                .append("trainTypeId", trip.trainTypeId()).append("routeId", trip.routeId())
                .append("startingTime", trip.startingTime()).append("startingStationId", trip.startingStationId())
                .append("stationsId", trip.stationsId()).append("terminalStationId", trip.terminalStationId())
                .append("endTime", trip.endTime());
        collection.replaceOne(eq("_id", id), doc, new ReplaceOptions().upsert(true));
    }
    void delete(TripId id) { requireWriter(); collection.deleteOne(eq("_id", key(id))); }
    private void requireWriter() {
        if (!writesEnabled || !ownership.permits("travel"))
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "Travel writes disabled");
    }
    @PreDestroy void close() { client.close(); }
}
