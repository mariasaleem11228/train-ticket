package trainticket.ticketoffice;

import com.mongodb.ConnectionString;
import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;
import com.mongodb.client.MongoCollection;
import com.mongodb.client.model.Filters;
import com.mongodb.client.model.Updates;
import com.mongodb.client.result.UpdateResult;
import jakarta.annotation.PreDestroy;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.bson.Document;
import org.bson.types.ObjectId;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Repository;
import org.springframework.web.server.ResponseStatusException;
import trainticket.runtime.WriteOwnership;

@Repository
@ConditionalOnProperty(name = "modulith.ticketoffice.enabled", havingValue = "true")
class TicketOfficeRepository {
    private final MongoClient client;
    private final MongoCollection<Document> offices;
    private final boolean writesEnabled;
    private final WriteOwnership ownership;

    TicketOfficeRepository(@Value("${modulith.ticketoffice.mongo-uri}") String uri,
            @Value("${modulith.ticketoffice.writes-enabled:false}") boolean writesEnabled,
            WriteOwnership ownership) {
        ConnectionString connection = new ConnectionString(uri);
        if (connection.getDatabase() == null) throw new IllegalArgumentException("Ticket Office database required");
        this.client = MongoClients.create(connection);
        this.offices = client.getDatabase(connection.getDatabase()).getCollection("office");
        this.writesEnabled = writesEnabled;
        this.ownership = ownership;
    }

    @PreDestroy void close() { client.close(); }

    List<Map<String,Object>> all() { return find(new Document()); }

    List<Map<String,Object>> specific(String province, String city, String region) {
        return find(region(province, city, region));
    }

    private List<Map<String,Object>> find(Document filter) {
        List<Map<String,Object>> result = new ArrayList<>();
        for (Document document : offices.find(filter)) result.add(convert(document));
        return result;
    }

    Map<String,Object> add(String province, String city, String region, Map<String,Object> office) {
        guard();
        Document value = new Document("officeName", office.get("officeName"))
                .append("address", office.get("address"))
                .append("workTime", office.get("workTime"))
                .append("windowNum", office.get("windowNum"));
        return result(offices.updateOne(region(province, city, region), Updates.push("offices", value)));
    }

    Map<String,Object> delete(String province, String city, String region, String officeName) {
        guard();
        return result(offices.updateOne(region(province, city, region),
                Updates.pull("offices", new Document("officeName", officeName))));
    }

    Map<String,Object> update(String province, String city, String region, String oldName, Map<String,Object> office) {
        guard();
        Document filter = region(province, city, region).append("offices.officeName", oldName);
        return result(offices.updateOne(filter, Updates.combine(
                Updates.set("offices.$.officeName", office.get("officeName")),
                Updates.set("offices.$.address", office.get("address")),
                Updates.set("offices.$.workTime", office.get("workTime")),
                Updates.set("offices.$.windowNum", office.get("windowNum")))));
    }

    private void guard() {
        if (!writesEnabled || !ownership.permits("ticketoffice"))
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "Ticket Office writes disabled");
    }

    private Document region(String province, String city, String region) {
        return new Document("province", province).append("city", city).append("region", region);
    }

    private Map<String,Object> result(UpdateResult update) {
        Map<String,Object> answer = new LinkedHashMap<>();
        answer.put("n", update.getMatchedCount());
        answer.put("nModified", update.getModifiedCount());
        answer.put("ok", 1);
        return answer;
    }

    @SuppressWarnings("unchecked")
    private Map<String,Object> convert(Document source) {
        Map<String,Object> result = new LinkedHashMap<>();
        source.forEach((key, value) -> result.put(key, convertValue(value)));
        return result;
    }

    private Object convertValue(Object value) {
        if (value instanceof ObjectId id) return id.toHexString();
        if (value instanceof Document document) return convert(document);
        if (value instanceof List<?> list) return list.stream().map(this::convertValue).toList();
        return value;
    }
}
