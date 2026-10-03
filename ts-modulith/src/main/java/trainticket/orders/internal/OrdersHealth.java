package trainticket.orders.internal;

import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.HealthIndicator;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;

@Component
@ConditionalOnProperty(name="modulith.orders.enabled", havingValue="true")
class OrdersHealth implements HealthIndicator {
    private final OrderRepository orders;
    OrdersHealth(OrderRepository orders) { this.orders=orders; }
    @Override public Health health() {
        try { orders.ping(); return Health.up().build(); }
        catch (Exception failure) { return Health.down().build(); }
    }
}
