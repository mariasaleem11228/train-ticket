package trainticket.user.internal;

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
import trainticket.runtime.WriteOwnership;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.UUID;

import static com.mongodb.client.model.Filters.eq;

@Repository
@ConditionalOnProperty(name="modulith.user.enabled",havingValue="true")
class UserRepository {
    private final MongoClient client;
    private final MongoCollection<Document> users;
    private final boolean writesEnabled;
    private final WriteOwnership ownership;

    UserRepository(@Value("${modulith.user.mongo-uri}") String uri,
                   @Value("${modulith.user.writes-enabled:false}") boolean writesEnabled,
                   WriteOwnership ownership) {
        ConnectionString connection=new ConnectionString(uri);
        client=MongoClients.create(MongoClientSettings.builder().applyConnectionString(connection)
                .uuidRepresentation(UuidRepresentation.JAVA_LEGACY).build());
        users=client.getDatabase(Objects.requireNonNull(connection.getDatabase(),"User database required"))
                .getCollection("user");
        this.writesEnabled=writesEnabled;this.ownership=ownership;
    }
    List<Document> all() {
        List<Document> result=new ArrayList<>();
        for (Document row:users.find())result.add(row);
        return result;
    }
    Document byName(String name) { return users.find(eq("userName",name)).first(); }
    Document byId(UUID id) { return users.find(eq("userId",id)).first(); }
    void save(Document user) { requireWriter();users.insertOne(user); }
    void delete(UUID id) { requireWriter();users.deleteMany(eq("userId",id)); }
    void requireWriter() {
        if (!writesEnabled || !ownership.permits("user"))
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,"User writes disabled");
    }
    @PreDestroy void close() { client.close(); }
}
