package trainticket.user;

import java.util.Map;
import java.util.UUID;
import org.springframework.http.ResponseEntity;

/** Published User operations for local modules. */
public interface UserOperations {
    Map<String,Object> all();
    ResponseEntity<Map<String,Object>> register(Map<String,Object> body);
    Map<String,Object> update(Map<String,Object> body);
    Map<String,Object> delete(UUID id);
}
