package trainticket.insidepayment.internal;

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
import trainticket.insidepayment.WalletMoney;
import trainticket.insidepayment.WalletPayment;
import trainticket.runtime.WriteOwnership;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import static com.mongodb.client.model.Filters.eq;

@Repository
@ConditionalOnProperty(name="modulith.inside-payment.enabled",havingValue="true")
class WalletRepository {
    private final MongoClient client;
    private final MongoCollection<Document> payments;
    private final MongoCollection<Document> monies;
    private final WriteOwnership ownership;
    private final boolean writesEnabled;

    WalletRepository(@Value("${modulith.inside-payment.mongo-uri}") String uri,
                     @Value("${modulith.inside-payment.writes-enabled:false}") boolean writesEnabled,
                     WriteOwnership ownership) {
        ConnectionString connection=new ConnectionString(uri);
        client=MongoClients.create(connection);
        var database=client.getDatabase(Objects.requireNonNull(connection.getDatabase(),"Inside Payment database required"));
        payments=database.getCollection("payment");
        monies=database.getCollection("addMoney");
        this.writesEnabled=writesEnabled;
        this.ownership=ownership;
    }

    List<WalletPayment> payments() {
        List<WalletPayment> rows=new ArrayList<>();
        for(Document row:payments.find())rows.add(payment(row));
        return rows;
    }
    List<WalletPayment> paymentsFor(String userId) {
        List<WalletPayment> rows=new ArrayList<>();
        for(Document row:payments.find(eq("userId",userId)))rows.add(payment(row));
        return rows;
    }
    List<WalletMoney> monies() {
        List<WalletMoney> rows=new ArrayList<>();
        for(Document row:monies.find())rows.add(money(row));
        return rows;
    }
    List<WalletMoney> moniesFor(String userId) {
        List<WalletMoney> rows=new ArrayList<>();
        for(Document row:monies.find(eq("userId",userId)))rows.add(money(row));
        return rows;
    }
    void save(WalletPayment row) {
        requireWriter();
        payments.insertOne(new Document("_id",row.id())
                .append("_class","inside_payment.entity.Payment")
                .append("orderId",row.orderId()).append("userId",row.userId())
                .append("price",row.price()).append("type",row.type()));
    }
    void save(WalletMoney row) {
        requireWriter();
        monies.insertOne(new Document("_id",row.id())
                .append("_class","inside_payment.entity.Money")
                .append("userId",row.userId()).append("money",row.money())
                .append("type",row.type()));
    }
    void requireWriter() {
        if(!writesEnabled||!ownership.permits("insidepayment"))
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,"Inside Payment writes disabled");
    }
    private WalletPayment payment(Document row) {
        return new WalletPayment(row.getString("_id"),value(row,"orderId"),value(row,"userId"),
                value(row,"price"),row.getString("type"));
    }
    private WalletMoney money(Document row) {
        return new WalletMoney(row.getString("_id"),value(row,"userId"),value(row,"money"),
                row.getString("type"));
    }
    private String value(Document row,String name) { return row.getString(name)==null?"":row.getString(name); }
    @PreDestroy void close() { client.close(); }
}
