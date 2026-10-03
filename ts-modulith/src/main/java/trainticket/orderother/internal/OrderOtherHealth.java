package trainticket.orderother.internal;

import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.HealthIndicator;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

@Component
@ConditionalOnProperty(name="modulith.order-other.enabled", havingValue="true")
class OrderOtherHealth implements HealthIndicator {
    private final OrderOtherRepository repository;
    OrderOtherHealth(OrderOtherRepository repository) { this.repository=repository; }
    @Override public Health health() {
        try { repository.ping(); return Health.up().build(); }
        catch (Exception failure) { return Health.down().build(); }
    }
}
