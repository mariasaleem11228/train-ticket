package trainticket.auth.internal;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import org.bson.Document;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriUtils;
import trainticket.auth.AuthOperations;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Base64;
import java.util.Date;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@ConditionalOnProperty(name="modulith.identity.enabled",havingValue="true")
class AuthController {
    private static final String SECRET=Base64.getEncoder().encodeToString("secret".getBytes(StandardCharsets.UTF_8));
    private final AuthRepository repository;
    private final AuthOperations operations;
    private final BCryptPasswordEncoder passwords=new BCryptPasswordEncoder();
    private final RestTemplate http=new RestTemplate();
    private final String verifyUrl;

    AuthController(AuthRepository repository,AuthOperations operations,
                   @Value("${modulith.identity.verify-url}") String verifyUrl) {
        this.repository=repository;this.operations=operations;this.verifyUrl=verifyUrl;
    }

    @GetMapping("/api/v1/auth/hello") String authHello() { return "hello"; }
    @GetMapping("/api/v1/users/hello") String usersHello() { return "Hello"; }

    @PostMapping("/api/v1/auth") ResponseEntity<Map<String,Object>> register(@RequestBody Map<String,Object> body) {
        UUID id=UUID.fromString(String.valueOf(body.get("userId")));
        String username=String.valueOf(body.get("userName"));
        String password=String.valueOf(body.get("password"));
        operations.createDefaultUser(id,username,password);
        return ResponseEntity.status(201).body(result(1,"SUCCESS",body));
    }

    @PostMapping("/api/v1/users/login") Map<String,Object> login(@RequestBody Map<String,Object> body,
                                                                     @RequestHeader HttpHeaders headers) {
        String username=(String)body.get("username");
        String password=(String)body.get("password");
        String code=(String)body.get("verificationCode");
        if (code!=null && !code.isEmpty()) {
            String path="/api/v1/verifycode/verify/"+UriUtils.encodePathSegment(code,StandardCharsets.UTF_8);
            HttpHeaders forwarded=new HttpHeaders();
            if (headers.getFirst(HttpHeaders.COOKIE)!=null)
                forwarded.set(HttpHeaders.COOKIE,headers.getFirst(HttpHeaders.COOKIE));
            Boolean valid=http.exchange(verifyUrl+path,HttpMethod.GET,
                    new org.springframework.http.HttpEntity<>(forwarded),Boolean.class).getBody();
            if (!Boolean.TRUE.equals(valid))return result(0,"Verification failed.",null);
        }
        Document user=repository.byName(username);
        if (user==null || password==null || !passwords.matches(password,user.getString("password")))
            return result(0,"Incorrect username or password.",null);
        UUID id=user.get("userId",UUID.class);
        List<String> roles=user.getList("roles",String.class);
        Claims claims=Jwts.claims().setSubject(username);
        claims.put("roles",roles);claims.put("id",id);
        Date now=new Date();
        String token=Jwts.builder().setClaims(claims).setIssuedAt(now)
                .setExpiration(new Date(now.getTime()+3600000))
                .signWith(SignatureAlgorithm.HS256,SECRET).compact();
        return result(1,"login success",Map.of("userId",id,"username",username,"token",token));
    }

    @GetMapping("/api/v1/users") List<Map<String,Object>> all() {
        List<Map<String,Object>> result=new ArrayList<>();
        for (Document user:repository.all()) {
            List<String> roles=user.getList("roles",String.class);
            Map<String,Object> row=new LinkedHashMap<>();
            row.put("userId",user.get("userId",UUID.class));
            row.put("username",user.getString("username"));
            row.put("password",user.getString("password"));
            row.put("roles",roles);
            row.put("enabled",true);row.put("accountNonExpired",true);
            row.put("accountNonLocked",true);row.put("credentialsNonExpired",true);
            row.put("authorities",roles.stream().map(role->Map.of("authority",role)).toList());
            result.add(row);
        }
        return result;
    }

    @DeleteMapping("/api/v1/users/{userId}") Map<String,Object> delete(@PathVariable UUID userId) {
        operations.deleteUser(userId);
        return result(1,"DELETE USER SUCCESS",null);
    }

    private Map<String,Object> result(int status,String message,Object data) {
        Map<String,Object> result=new LinkedHashMap<>();
        result.put("status",status);result.put("msg",message);result.put("data",data);
        return result;
    }
}
