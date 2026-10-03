package trainticket.security;

import java.util.List;

public interface SecurityOperations {
    SecurityResult<List<SecurityConfig>> all();
    SecurityResult<SecurityConfig> create(SecurityConfig info);
    SecurityResult<SecurityConfig> update(SecurityConfig info);
    SecurityResult<String> delete(String id);
    SecurityResult<String> check(String accountId);
}
