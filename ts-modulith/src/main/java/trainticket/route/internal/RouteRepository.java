package trainticket.route.internal;

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
import org.bson.types.ObjectId;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Repository;
import org.springframework.web.server.ResponseStatusException;
import trainticket.route.Route;
import trainticket.runtime.WriteOwnership;
import static com.mongodb.client.model.Filters.eq;

/** Reads the original routes collection without running the legacy seeder. */
@Repository
@ConditionalOnProperty(name="modulith.route.enabled", havingValue="true")
class RouteRepository {
    private final MongoClient client;
    private final MongoCollection<Document> collection;
    private final boolean writesEnabled;
    private final WriteOwnership ownership;
    RouteRepository(@Value("${modulith.route.mongo-uri}") String uri,
                    @Value("${modulith.route.writes-enabled:false}") boolean writesEnabled,
                    WriteOwnership ownership) {
        ConnectionString connection=new ConnectionString(uri);
        client=MongoClients.create(uri);
        collection=client.getDatabase(Objects.requireNonNull(connection.getDatabase(),"Route database required"))
                .getCollection("routes");
        this.writesEnabled=writesEnabled;
        this.ownership=ownership;
    }
    private Object mongoId(String id) { return ObjectId.isValid(id) ? new ObjectId(id) : id; }
    Route find(String id) { return from(collection.find(eq("_id",mongoId(id))).first()); }
    List<Route> all() {
        List<Route> result=new ArrayList<>();
        for (Document doc:collection.find()) result.add(from(doc));
        return result;
    }
    void save(Route route) {
        requireWriter();
        Object id=mongoId(route.getId());
        Document doc=new Document("_id",id).append("stations",route.getStations())
                .append("distances",route.getDistances())
                .append("startStationId",route.getStartStationId())
                .append("terminalStationId",route.getTerminalStationId())
                .append("_class","route.entity.Route");
        collection.replaceOne(eq("_id",id),doc,new ReplaceOptions().upsert(true));
    }
    void delete(String id) { requireWriter(); collection.deleteOne(eq("_id",mongoId(id))); }
    private Route from(Document doc) {
        if (doc==null) return null;
        List<String> stations=doc.getList("stations",String.class);
        List<Integer> distances=doc.getList("distances",Integer.class);
        return new Route(doc.get("_id").toString(),stations,distances,
                doc.getString("startStationId"),doc.getString("terminalStationId"));
    }
    private void requireWriter() {
        if (!writesEnabled || !ownership.permits("route"))
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,"Route writes disabled");
    }
    @PreDestroy void close() { client.close(); }
}
