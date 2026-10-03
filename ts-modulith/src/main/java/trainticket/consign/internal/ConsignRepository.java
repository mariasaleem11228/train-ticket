package trainticket.consign.internal;

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
import trainticket.consign.ConsignRecord;
import trainticket.runtime.WriteOwnership;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.UUID;

import static com.mongodb.client.model.Filters.eq;

@Repository
@ConditionalOnProperty(name="modulith.consign.enabled",havingValue="true")
class ConsignRepository {
    private final MongoClient client;
    private final MongoCollection<Document> collection;
    private final boolean writesEnabled;
    private final WriteOwnership ownership;
    ConsignRepository(@Value("${modulith.consign.mongo-uri}") String uri,
                      @Value("${modulith.consign.writes-enabled:false}") boolean writesEnabled,
                      WriteOwnership ownership) {
        ConnectionString connection=new ConnectionString(uri);
        client=MongoClients.create(MongoClientSettings.builder().applyConnectionString(connection)
                .uuidRepresentation(UuidRepresentation.JAVA_LEGACY).build());
        collection=client.getDatabase(Objects.requireNonNull(connection.getDatabase(),"Consign database required"))
                .getCollection("consign_record");
        this.writesEnabled=writesEnabled;
        this.ownership=ownership;
    }
    ConsignRecord byId(UUID id) { return from(collection.find(eq("_id",id)).first()); }
    ConsignRecord byOrder(UUID orderId) { return from(collection.find(eq("orderId",orderId)).first()); }
    List<ConsignRecord> byAccount(UUID accountId) { return list("accountId",accountId); }
    List<ConsignRecord> byConsignee(String consignee) { return list("consignee",consignee); }
    private List<ConsignRecord> list(String field,Object value) {
        List<ConsignRecord> records=new ArrayList<>();
        for (Document row:collection.find(eq(field,value))) records.add(from(row));
        return records;
    }
    void save(ConsignRecord record) {
        if (!writesEnabled || !ownership.permits("consign"))
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,"Consign writes disabled");
        Document row=new Document("_id",record.id()).append("_class","consign.entity.ConsignRecord")
                .append("orderId",record.orderId()).append("accountId",record.accountId())
                .append("handleDate",record.handleDate()).append("targetDate",record.targetDate())
                .append("from",record.from()).append("to",record.to())
                .append("consignee",record.consignee()).append("phone",record.phone())
                .append("weight",record.weight()).append("price",record.price());
        collection.replaceOne(eq("_id",record.id()),row,new ReplaceOptions().upsert(true));
    }
    private ConsignRecord from(Document row) {
        return row==null?null:new ConsignRecord(row.get("_id",UUID.class),row.get("orderId",UUID.class),
                row.get("accountId",UUID.class),row.getString("handleDate"),row.getString("targetDate"),
                row.getString("from"),row.getString("to"),row.getString("consignee"),row.getString("phone"),
                row.getDouble("weight"),row.getDouble("price"));
    }
    @PreDestroy void close() { client.close(); }
}
