package trainticket.contacts.internal;

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
import trainticket.contacts.Contact;
import trainticket.runtime.WriteOwnership;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.UUID;
import static com.mongodb.client.model.Filters.eq;

@Repository
@ConditionalOnProperty(name="modulith.contacts.enabled", havingValue="true")
class ContactsRepository {
    private final MongoClient client;
    private final MongoCollection<Document> collection;
    private final boolean writesEnabled;
    private final WriteOwnership ownership;

    ContactsRepository(@Value("${modulith.contacts.mongo-uri}") String uri,
                       @Value("${modulith.contacts.writes-enabled:false}") boolean writesEnabled,
                       WriteOwnership ownership) {
        ConnectionString connection = new ConnectionString(uri);
        client = MongoClients.create(MongoClientSettings.builder().applyConnectionString(connection)
                .uuidRepresentation(UuidRepresentation.JAVA_LEGACY).build());
        collection = client.getDatabase(Objects.requireNonNull(connection.getDatabase(), "Contacts database required"))
                .getCollection("contacts");
        this.writesEnabled = writesEnabled;
        this.ownership = ownership;
    }

    Contact find(String id) { return from(collection.find(eq("_id", UUID.fromString(id))).first()); }
    List<Contact> byAccount(String accountId) {
        List<Contact> contacts = new ArrayList<>();
        for (Document row : collection.find(eq("accountId", UUID.fromString(accountId)))) contacts.add(from(row));
        return contacts;
    }
    List<Contact> all() {
        List<Contact> contacts = new ArrayList<>();
        for (Document row : collection.find()) contacts.add(from(row));
        return contacts;
    }
    void save(Contact contact) {
        requireWriter();
        UUID id = UUID.fromString(contact.id());
        Document row = new Document("_id", id).append("_class", "contacts.entity.Contacts")
                .append("accountId", UUID.fromString(contact.accountId()))
                .append("name", contact.name()).append("documentType", contact.documentType())
                .append("documentNumber", contact.documentNumber()).append("phoneNumber", contact.phoneNumber());
        collection.replaceOne(eq("_id", id), row, new ReplaceOptions().upsert(true));
    }
    void delete(String id) { requireWriter(); collection.deleteOne(eq("_id", UUID.fromString(id))); }
    private Contact from(Document row) {
        return row == null ? null : new Contact(row.get("_id", UUID.class).toString(),
                row.get("accountId", UUID.class).toString(), row.getString("name"),
                row.getInteger("documentType", 0), row.getString("documentNumber"), row.getString("phoneNumber"));
    }
    private void requireWriter() {
        if (!writesEnabled || !ownership.permits("contacts"))
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "Contacts writes disabled");
    }
    @PreDestroy void close() { client.close(); }
}
