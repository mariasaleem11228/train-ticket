package trainticket.user.internal;

import org.bson.Document;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import trainticket.auth.AuthOperations;
import trainticket.user.UserOperations;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@ConditionalOnProperty(name="modulith.user.enabled",havingValue="true")
@RequestMapping("/api/v1/userservice/users")
class UserController implements UserOperations {
    private final UserRepository repository;
    private final AuthOperations auth;
    UserController(UserRepository repository,AuthOperations auth) {
        this.repository=repository;this.auth=auth;
    }

    @GetMapping("/hello") String hello() { return "Hello"; }
    @Override @GetMapping public Map<String,Object> all() {
        List<Map<String,Object>> users=new ArrayList<>();
        for (Document row:repository.all())users.add(toUser(row));
        return users.isEmpty()?response(0,"NO User",null):response(1,"Success",users);
    }
    @GetMapping("/{name}") Map<String,Object> byName(@PathVariable String name) {
        Document user=repository.byName(name);
        return user==null?response(0,"No User",null):response(1,"Find User Success",toUser(user));
    }
    @GetMapping("/id/{id}") Map<String,Object> byId(@PathVariable UUID id) {
        Document user=repository.byId(id);
        return user==null?response(0,"No User",null):response(1,"Find User Success",toUser(user));
    }
    @Override @PostMapping("/register") public ResponseEntity<Map<String,Object>> register(@RequestBody Map<String,Object> body) {
        UUID id=body.get("userId")==null?UUID.randomUUID():UUID.fromString(String.valueOf(body.get("userId")));
        String name=(String)body.get("userName");
        if (repository.byName(name)!=null)
            return ResponseEntity.status(201).body(response(0,"USER HAS ALREADY EXISTS",null));
        repository.requireWriter();
        Document user=from(body,id);
        auth.createDefaultUser(id,name,(String)body.get("password"));
        repository.save(user);
        return ResponseEntity.status(201).body(response(1,"REGISTER USER SUCCESS",toUser(user)));
    }
    @Override @DeleteMapping("/{id}") public Map<String,Object> delete(@PathVariable UUID id) {
        if (repository.byId(id)==null)return response(0,"USER NOT EXISTS",null);
        repository.requireWriter();
        auth.deleteUser(id);
        repository.delete(id);
        return response(1,"DELETE SUCCESS",null);
    }
    @Override @PutMapping public Map<String,Object> update(@RequestBody Map<String,Object> body) {
        UUID id=UUID.fromString(String.valueOf(body.get("userId")));
        if (repository.byId(id)==null)return response(0,"USER NOT EXISTS",null);
        repository.requireWriter();
        Document updated=from(body,id);
        repository.delete(id);
        repository.save(updated);
        return response(1,"SAVE USER SUCCESS",toUser(updated));
    }
    private Document from(Map<String,Object> body,UUID id) {
        return new Document("_class","user.entity.User").append("userId",id)
                .append("userName",body.get("userName"))
                .append("password",body.get("password"))
                .append("gender",number(body.get("gender")))
                .append("documentType",number(body.get("documentType")))
                .append("documentNum",body.get("documentNum"))
                .append("email",body.get("email"));
    }
    private int number(Object value) { return value instanceof Number n?n.intValue():0; }
    private Map<String,Object> toUser(Document row) {
        Map<String,Object> user=new LinkedHashMap<>();
        user.put("userId",row.get("userId",UUID.class));
        user.put("userName",row.getString("userName"));
        user.put("password",row.getString("password"));
        user.put("gender",row.getInteger("gender",0));
        user.put("documentType",row.getInteger("documentType",0));
        user.put("documentNum",row.getString("documentNum"));
        user.put("email",row.getString("email"));
        return user;
    }
    private Map<String,Object> response(int status,String message,Object data) {
        Map<String,Object> response=new LinkedHashMap<>();
        response.put("status",status);response.put("msg",message);response.put("data",data);
        return response;
    }
}
