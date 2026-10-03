package trainticket.contacts.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import trainticket.contacts.Contact;
import trainticket.contacts.ContactResult;
import trainticket.contacts.ContactsOperations;
import java.util.List;
import java.util.Objects;
import java.util.UUID;

/** Matches the deployed 0.2.0 Mongo-backed Contacts behavior. */
@Service
@ConditionalOnProperty(name="modulith.contacts.enabled", havingValue="true")
class ContactsApplicationService implements ContactsOperations {
    private final ContactsRepository repository;
    ContactsApplicationService(ContactsRepository repository) { this.repository = repository; }

    public ContactResult<List<Contact>> all() {
        List<Contact> contacts = repository.all();
        return contacts.isEmpty() ? new ContactResult<>(0, "No content", null)
                : new ContactResult<>(1, "Success", contacts);
    }
    public ContactResult<List<Contact>> byAccount(String accountId) {
        return new ContactResult<>(1, "Success", repository.byAccount(accountId));
    }
    public ContactResult<Contact> byId(String id) {
        Contact contact = repository.find(id);
        return contact == null ? new ContactResult<>(0, "No contacts according to contacts id", null)
                : new ContactResult<>(1, "Success", contact);
    }
    public ContactResult<Contact> create(Contact input) {
        Contact contact = new Contact(UUID.randomUUID().toString(), input.accountId(), input.name(),
                input.documentType(), input.documentNumber(), input.phoneNumber());
        boolean duplicate = repository.byAccount(contact.accountId()).stream().anyMatch(existing ->
                existing.documentType() == contact.documentType()
                && Objects.equals(existing.documentNumber(), contact.documentNumber()));
        if (duplicate) return new ContactResult<>(0, "Contacts already exists", null);
        repository.save(contact);
        return new ContactResult<>(1, "Create contacts success", contact);
    }
    public ContactResult<Contact> createAdmin(Contact input) {
        Contact contact = new Contact(UUID.randomUUID().toString(), input.accountId(), input.name(),
                input.documentType(), input.documentNumber(), input.phoneNumber());
        Contact old = repository.find(contact.id());
        if (old != null) return new ContactResult<>(0, "Already Exists", old);
        repository.save(contact);
        return new ContactResult<>(1, "Create Success", null);
    }
    public ContactResult<Contact> modify(Contact input) {
        Contact old = repository.find(input.id());
        if (old == null) return new ContactResult<>(0, "Contacts not found", null);
        Contact updated = new Contact(old.id(), old.accountId(), input.name(), input.documentType(),
                input.documentNumber(), input.phoneNumber());
        repository.save(updated);
        return new ContactResult<>(1, "Modify success", updated);
    }
    public ContactResult<String> delete(String id) {
        repository.delete(id);
        return repository.find(id) == null ? new ContactResult<>(1, "Delete success", id)
                : new ContactResult<>(0, "Delete failed", id);
    }
}
