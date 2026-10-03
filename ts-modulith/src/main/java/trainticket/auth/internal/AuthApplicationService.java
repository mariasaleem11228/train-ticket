package trainticket.auth.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;
import trainticket.auth.AuthOperations;

import java.util.UUID;

@Service
@ConditionalOnProperty(name="modulith.identity.enabled",havingValue="true")
class AuthApplicationService implements AuthOperations {
    private final AuthRepository repository;
    private final BCryptPasswordEncoder passwords=new BCryptPasswordEncoder();
    AuthApplicationService(AuthRepository repository) { this.repository=repository; }
    @Override public void createDefaultUser(UUID id,String username,String password) {
        repository.create(id,username,passwords.encode(password));
    }
    @Override public void deleteUser(UUID id) { repository.delete(id); }
}
