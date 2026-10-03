package trainticket.auth.internal;

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
@ConditionalOnProperty(name="modulith.identity.enabled",havingValue="true")
class AuthRepository {
    private final MongoClient client;
    private final MongoCollection<Document> users;
    private final boolean writesEnabled;
    private final WriteOwnership ownership;

    AuthRepository(@Value("${modulith.identity.mongo-uri}") String uri,
                   @Value("${modulith.identity.writes-enabled:false}") boolean writesEnabled,
                   WriteOwnership ownership) {
        ConnectionString connection=new ConnectionString(uri);
        client=MongoClients.create(MongoClientSettings.builder().applyConnectionString(connection)
                .uuidRepresentation(UuidRepresentation.JAVA_LEGACY).build());
        users=client.getDatabase(Objects.requireNonNull(connection.getDatabase(),"Auth database required"))
                .getCollection("user");
        this.writesEnabled=writesEnabled;
        this.ownership=ownership;
    }

    Document byName(String name) { return users.find(eq("username",name)).first(); }
    List<Document> all() {
        List<Document> result=new ArrayList<>();
        for (Document row:users.find())result.add(row);
        return result;
    }
    void create(UUID id,String name,String hashedPassword) {
        requireWriter();
        users.insertOne(new Document("_class","auth.entity.User")
                .append("userId",id).append("username",name).append("password",hashedPassword)
                .append("roles",List.of("ROLE_USER")));
    }
    void delete(UUID id) { requireWriter();users.deleteMany(eq("userId",id)); }
    private void requireWriter() {
        if (!writesEnabled || !ownership.permits("auth"))
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,"Auth writes disabled");
    }
    @PreDestroy void close() { client.close(); }
}
