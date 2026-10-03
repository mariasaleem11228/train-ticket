package trainticket.contacts;

import java.util.List;

public interface ContactsOperations {
    ContactResult<List<Contact>> all();
    ContactResult<List<Contact>> byAccount(String accountId);
    ContactResult<Contact> byId(String id);
    ContactResult<Contact> create(Contact contact);
    ContactResult<Contact> createAdmin(Contact contact);
    ContactResult<Contact> modify(Contact contact);
    ContactResult<String> delete(String id);
}
