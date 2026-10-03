package trainticket.contacts.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import trainticket.contacts.Contact;
import trainticket.contacts.ContactsOperations;

@RestController
@ConditionalOnProperty(name="modulith.contacts.enabled", havingValue="true")
@RequestMapping("/api/v1/contactservice/contacts")
class ContactsController {
    private final ContactsOperations contacts;
    ContactsController(ContactsOperations contacts) { this.contacts = contacts; }

    @GetMapping("/welcome") String welcome() { return "Welcome to [ Contacts Service ] !"; }
    @CrossOrigin(origins="*") @GetMapping Object all() { return contacts.all(); }
    @CrossOrigin(origins="*") @GetMapping("/account/{accountId}") Object byAccount(@PathVariable String accountId) {
        return contacts.byAccount(accountId);
    }
    @CrossOrigin(origins="*") @GetMapping("/{id}") Object byId(@PathVariable String id) { return contacts.byId(id); }
    @CrossOrigin(origins="*") @PostMapping ResponseEntity<?> create(@RequestBody Contact body) {
        return ResponseEntity.status(201).body(contacts.create(body));
    }
    @CrossOrigin(origins="*") @PostMapping("/admin") ResponseEntity<?> createAdmin(@RequestBody Contact body) {
        return ResponseEntity.status(201).body(contacts.createAdmin(body));
    }
    @CrossOrigin(origins="*") @PutMapping Object modify(@RequestBody Contact body) { return contacts.modify(body); }
    @CrossOrigin(origins="*") @DeleteMapping("/{id}") Object delete(@PathVariable String id) {
        return contacts.delete(id);
    }
}
