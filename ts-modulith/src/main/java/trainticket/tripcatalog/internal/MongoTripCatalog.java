package trainticket.tripcatalog.internal;

import com.mongodb.ConnectionString;
import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.model.ReplaceOptions;
import jakarta.annotation.PreDestroy;
import org.bson.Document;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Repository;
import org.springframework.web.server.ResponseStatusException;
import trainticket.runtime.WriteOwnership;
import trainticket.tripcatalog.TripCatalogOperations;
import trainticket.tripcatalog.TripSnapshot;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

import static com.mongodb.client.model.Filters.eq;

/** Reads and writes the existing, separate Travel and Travel2 Mongo collections. */
@Repository
class MongoTripCatalog implements TripCatalogOperations {
    private final MongoClient standardClient;
    private final MongoClient otherClient;
    private final MongoCollection<Document> standardTrips;
    private final MongoCollection<Document> otherTrips;
    private final boolean standardWrites;
    private final boolean otherWrites;
    private final WriteOwnership ownership;

    MongoTripCatalog(@Value("${modulith.travel.mongo-uri}") String standardUri,
                     @Value("${modulith.travel2.mongo-uri}") String otherUri,
                     @Value("${modulith.travel.writes-enabled:false}") boolean standardWrites,
                     @Value("${modulith.travel2.writes-enabled:false}") boolean otherWrites,
                     WriteOwnership ownership) {
        standardClient=MongoClients.create(standardUri);
        otherClient=MongoClients.create(otherUri);
        standardTrips=standardClient.getDatabase(Objects.requireNonNull(
                new ConnectionString(standardUri).getDatabase(),"Travel database required"))
                .getCollection("trip");
        otherTrips=otherClient.getDatabase(Objects.requireNonNull(
                new ConnectionString(otherUri).getDatabase(),"Travel2 database required"))
                .getCollection("trip");
        this.standardWrites=standardWrites;
        this.otherWrites=otherWrites;
        this.ownership=ownership;
    }
    private MongoCollection<Document> collection(boolean standard) {
        return standard ? standardTrips : otherTrips;
    }
    private Document key(String id) {
        if (id==null || id.length()<2) throw new IllegalArgumentException("Invalid trip ID");
        return new Document("type",id.substring(0,1)).append("number",id.substring(1));
    }
    private TripSnapshot from(Document doc) {
        if (doc==null)return null;
        Document id=doc.get("_id",Document.class);
        return new TripSnapshot(id.getString("type")+id.getString("number"),
                doc.getString("trainTypeId"),doc.getString("routeId"),doc.getDate("startingTime"),
                doc.getString("startingStationId"),doc.getString("stationsId"),
                doc.getString("terminalStationId"),doc.getDate("endTime"));
    }
    public TripSnapshot find(String id,boolean standard) {
        return from(collection(standard).find(eq("_id",key(id))).first());
    }
    public List<TripSnapshot> all(boolean standard) {
        List<TripSnapshot> result=new ArrayList<>();
        for(Document doc:collection(standard).find())result.add(from(doc));
        return result;
    }
    public List<TripSnapshot> byRoute(String routeId,boolean standard) {
        List<TripSnapshot> result=new ArrayList<>();
        for(Document doc:collection(standard).find(eq("routeId",routeId)))result.add(from(doc));
        return result;
    }
    public void save(TripSnapshot trip,boolean standard) {
        requireWriter(standard);
        Document id=key(trip.tripId());
        Document doc=new Document("_id",id).append("_class",
                standard?"travel.entity.Trip":"travel2.entity.Trip")
                .append("trainTypeId",trip.trainTypeId()).append("routeId",trip.routeId())
                .append("startingTime",trip.startingTime())
                .append("startingStationId",trip.startingStationId())
                .append("stationsId",trip.stationsId())
                .append("terminalStationId",trip.terminalStationId())
                .append("endTime",trip.endTime());
        collection(standard).replaceOne(eq("_id",id),doc,new ReplaceOptions().upsert(true));
    }
    public void delete(String tripId,boolean standard) {
        requireWriter(standard);
        collection(standard).deleteOne(eq("_id",key(tripId)));
    }
    private void requireWriter(boolean standard) {
        if (!(standard?standardWrites:otherWrites) || !ownership.permits(standard?"travel":"travel2"))
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,"Travel writes disabled");
    }
    @PreDestroy void close() { standardClient.close();otherClient.close(); }
}
