package trainticket.auth;

import java.util.UUID;

/** Operations published to the User module for identity lifecycle changes. */
public interface AuthOperations {
    void createDefaultUser(UUID id,String username,String password);
    void deleteUser(UUID id);
}
