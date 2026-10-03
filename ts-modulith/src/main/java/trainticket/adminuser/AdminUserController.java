package trainticket.adminuser;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.*;
import trainticket.user.UserOperations;

/** Admin facade over the published User API. */
@RestController
@RequestMapping("/api/v1/adminuserservice/users")
@ConditionalOnProperty(name = "modulith.adminuser.enabled", havingValue = "true")
class AdminUserController {
    private final UserOperations users;

    AdminUserController(UserOperations users) { this.users = users; }

    @GetMapping("/welcome") String welcome() { return "Welcome to [ AdminUser Service ] !"; }

    @GetMapping Map<String,Object> all() {
        Map<String,Object> result = users.all();
        return successful(result) ? result : failure("get all users error");
    }

    @PostMapping Map<String,Object> create(@RequestBody Map<String,Object> body) {
        Map<String,Object> result = users.register(body).getBody();
        return successful(result) ? result : failure("Add user error");
    }

    @PutMapping Map<String,Object> update(@RequestBody Map<String,Object> body) {
        Map<String,Object> result = users.update(body);
        return successful(result) ? result : failure("Update user error");
    }

    @DeleteMapping("/{id}") Map<String,Object> delete(@PathVariable UUID id) {
        Map<String,Object> result = users.delete(id);
        return successful(result) ? result : failure("delete user error");
    }

    private boolean successful(Map<String,Object> result) {
        return result != null && result.get("status") instanceof Number status && status.intValue() == 1;
    }

    private Map<String,Object> failure(String message) {
        Map<String,Object> result = new LinkedHashMap<>();
        result.put("status",0);
        result.put("msg",message);
        result.put("data",null);
        return result;
    }
}
