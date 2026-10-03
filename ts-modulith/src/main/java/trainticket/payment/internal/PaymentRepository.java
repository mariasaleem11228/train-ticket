package trainticket.payment.internal;

import com.mongodb.ConnectionString;
import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;
import com.mongodb.client.MongoCollection;
import jakarta.annotation.PreDestroy;
import org.bson.Document;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Repository;
import org.springframework.web.server.ResponseStatusException;
import trainticket.payment.MoneyRecord;
import trainticket.payment.PaymentRecord;
import trainticket.runtime.WriteOwnership;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import static com.mongodb.client.model.Filters.eq;

@Repository
@ConditionalOnProperty(name="modulith.payment.enabled", havingValue="true")
class PaymentRepository {
    private final MongoClient client;
    private final MongoCollection<Document> payments;
    private final MongoCollection<Document> money;
    private final WriteOwnership ownership;
    private final boolean writesEnabled;

    PaymentRepository(@Value("${modulith.payment.mongo-uri}") String uri,
                      @Value("${modulith.payment.writes-enabled:false}") boolean writesEnabled,
                      WriteOwnership ownership) {
        ConnectionString connection=new ConnectionString(uri);
        client=MongoClients.create(connection);
        var database=client.getDatabase(Objects.requireNonNull(connection.getDatabase(),"Payment database required"));
        payments=database.getCollection("payment");
        money=database.getCollection("addMoney");
        this.writesEnabled=writesEnabled;
        this.ownership=ownership;
    }

    PaymentRecord byOrderId(String orderId) {
        Document row=payments.find(eq("orderId",orderId)).first();
        return row==null?null:from(row);
    }
    List<PaymentRecord> all() {
        List<PaymentRecord> rows=new ArrayList<>();
        for(Document row:payments.find())rows.add(from(row));
        return rows;
    }
    void insert(PaymentRecord payment) {
        requireWriter();
        payments.insertOne(new Document("_id",payment.id())
                .append("_class","com.trainticket.entity.Payment")
                .append("orderId",payment.orderId()).append("userId",payment.userId())
                .append("price",payment.price()));
    }
    void addMoney(MoneyRecord value) {
        requireWriter();
        money.insertOne(new Document("_class","com.trainticket.entity.Money")
                .append("userId",value.userId()).append("money",value.money()));
    }
    private PaymentRecord from(Document row) {
        // The deployed Payment constructor initializes absent legacy fields to "".
        return new PaymentRecord(row.getString("_id"),row.getString("orderId"),
                row.getString("userId") == null ? "" : row.getString("userId"),row.getString("price"));
    }
    private void requireWriter() {
        if(!writesEnabled||!ownership.permits("payment"))
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,"Payment writes disabled");
    }
    @PreDestroy void close() { client.close(); }
}
