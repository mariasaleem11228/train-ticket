package trainticket.notification.internal;

import com.mongodb.ConnectionString;
import com.mongodb.MongoClientSettings;
import com.mongodb.client.MongoClient;
import com.mongodb.client.MongoClients;
import com.mongodb.client.MongoCollection;
import jakarta.annotation.PreDestroy;
import org.bson.Document;
import org.bson.UuidRepresentation;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Repository;
import org.springframework.web.server.ResponseStatusException;
import trainticket.notification.NotifyInfo;
import trainticket.runtime.WriteOwnership;
import java.util.Objects;

@Repository
@ConditionalOnProperty(name="modulith.notification.enabled",havingValue="true")
class NotificationRepository {
    private final MongoClient client;
    private final MongoCollection<Document> collection;
    private final boolean writesEnabled;
    private final WriteOwnership ownership;
    NotificationRepository(@Value("${modulith.notification.mongo-uri}") String uri,
                           @Value("${modulith.notification.writes-enabled:false}") boolean writesEnabled,
                           WriteOwnership ownership) {
        ConnectionString connection=new ConnectionString(uri);
        client=MongoClients.create(MongoClientSettings.builder().applyConnectionString(connection)
                .uuidRepresentation(UuidRepresentation.JAVA_LEGACY).build());
        collection=client.getDatabase(Objects.requireNonNull(connection.getDatabase())).getCollection("notifyInfo");
        this.writesEnabled=writesEnabled;this.ownership=ownership;
    }
    void save(NotifyInfo info) {
        if (!writesEnabled || !ownership.permits("notification"))
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,"Notification writes disabled");
        Document row=new Document("_id",info.id()).append("_class","notification.entity.NotifyInfo")
                .append("sendStatus",info.sendStatus()).append("email",info.email())
                .append("orderNumber",info.orderNumber()).append("username",info.username())
                .append("startingPlace",info.startingPlace()).append("endPlace",info.endPlace())
                .append("startingTime",info.startingTime()).append("date",info.date())
                .append("seatClass",info.seatClass()).append("seatNumber",info.seatNumber())
                .append("price",info.price());
        collection.insertOne(row);
    }
    @PreDestroy void close() { client.close(); }
}
