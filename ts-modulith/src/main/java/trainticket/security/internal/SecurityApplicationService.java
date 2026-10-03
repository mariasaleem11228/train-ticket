package trainticket.security.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import trainticket.orderother.OrderOtherOperations;
import trainticket.orders.OrderOperations;
import trainticket.security.SecurityConfig;
import trainticket.security.SecurityOperations;
import trainticket.security.SecurityResult;
import java.util.Date;
import java.util.List;
import java.util.UUID;

/** Order policy from deployed 0.2.0 Security service. */
@Service
@ConditionalOnProperty(name="modulith.security.enabled", havingValue="true")
class SecurityApplicationService implements SecurityOperations {
    private final SecurityRepository repository;
    private final OrderOperations orders;
    private final OrderOtherOperations orderOther;
    SecurityApplicationService(SecurityRepository repository, OrderOperations orders,
                               OrderOtherOperations orderOther) {
        this.repository = repository;
        this.orders = orders;
        this.orderOther = orderOther;
    }
    public SecurityResult<List<SecurityConfig>> all() {
        List<SecurityConfig> policies = repository.all();
        return policies.isEmpty() ? new SecurityResult<>(0, "No Content", null)
                : new SecurityResult<>(1, "Success", policies);
    }
    public SecurityResult<SecurityConfig> create(SecurityConfig info) {
        if (repository.findByName(info.getName()) != null)
            return new SecurityResult<>(0, "Security Config Already Exist", null);
        SecurityConfig policy = copy(info);
        policy.setId(UUID.randomUUID());
        repository.save(policy);
        return new SecurityResult<>(1, "Success", policy);
    }
    public SecurityResult<SecurityConfig> update(SecurityConfig info) {
        SecurityConfig policy = repository.findById(info.getId());
        if (policy == null) return new SecurityResult<>(0, "Security Config Not Exist", null);
        policy.setName(info.getName());
        policy.setValue(info.getValue());
        policy.setDescription(info.getDescription());
        repository.save(policy);
        return new SecurityResult<>(1, "Success", policy);
    }
    public SecurityResult<String> delete(String id) {
        UUID value = UUID.fromString(id);
        repository.delete(value);
        return repository.findById(value) == null ? new SecurityResult<>(1, "Success", id)
                : new SecurityResult<>(0, "Reason Not clear", id);
    }
    public SecurityResult<String> check(String accountId) {
        Date now = new Date();
        trainticket.orders.OrderSecurity first =
                (trainticket.orders.OrderSecurity)orders.checkSecurityAboutOrder(now, accountId).getData();
        trainticket.orderother.OrderSecurity second =
                (trainticket.orderother.OrderSecurity)orderOther.checkSecurityAboutOrder(now, accountId).getData();
        int lastHour = first.getOrderNumInLastOneHour() + second.getOrderNumInLastOneHour();
        int valid = first.getOrderNumOfValidOrder() + second.getOrderNumOfValidOrder();
        int hourlyLimit = Integer.parseInt(repository.findByName("max_order_1_hour").getValue());
        int validLimit = Integer.parseInt(repository.findByName("max_order_not_use").getValue());
        return lastHour > hourlyLimit || valid > validLimit
                ? new SecurityResult<>(0, "Too much order in last one hour or too much valid order", accountId)
                : new SecurityResult<>(1, "Success.r", accountId);
    }
    private SecurityConfig copy(SecurityConfig info) {
        SecurityConfig policy = new SecurityConfig();
        policy.setName(info.getName());
        policy.setValue(info.getValue());
        policy.setDescription(info.getDescription());
        return policy;
    }
}
