package trainticket.cancel.internal;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;
import trainticket.user.UserOperations;
import java.util.UUID;

/** Local User lookup used by cancellation. */
@Component
@ConditionalOnProperty(name="modulith.cancel.enabled",havingValue="true")
class CancelRemoteUser {
    private final UserOperations users;
    private final ObjectMapper mapper;
    CancelRemoteUser(UserOperations users,ObjectMapper mapper) {
        this.users=users;this.mapper=mapper;
    }
    JsonNode get(String accountId,String authorization) {
        return mapper.valueToTree(users.byId(UUID.fromString(accountId)));
    }
}
