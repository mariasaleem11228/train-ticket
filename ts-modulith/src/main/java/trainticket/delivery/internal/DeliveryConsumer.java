package trainticket.delivery.internal;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.core.Queue;
import org.springframework.amqp.rabbit.annotation.EnableRabbit;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.amqp.rabbit.listener.MessageListenerContainer;
import org.springframework.amqp.rabbit.listener.RabbitListenerEndpointRegistry;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import trainticket.runtime.WriteOwnership;

import java.util.UUID;

@Component
@ConditionalOnProperty(name = "modulith.delivery.enabled", havingValue = "true")
class DeliveryConsumer {
    private static final Logger LOG = LoggerFactory.getLogger(DeliveryConsumer.class);
    private final ObjectMapper mapper;
    private final DeliveryRepository repository;
    private final RabbitListenerEndpointRegistry registry;
    private final WriteOwnership ownership;
    private final boolean writesEnabled;

    DeliveryConsumer(ObjectMapper mapper, DeliveryRepository repository,
                     RabbitListenerEndpointRegistry registry, WriteOwnership ownership,
                     @Value("${modulith.delivery.writes-enabled:false}") boolean writesEnabled) {
        this.mapper = mapper;
        this.repository = repository;
        this.registry = registry;
        this.ownership = ownership;
        this.writesEnabled = writesEnabled;
    }

    @Scheduled(fixedDelay = 1000)
    void updateOwnership() {
        MessageListenerContainer listener = registry.getListenerContainer("delivery-module-consumer");
        if (listener == null) return;
        boolean active = writesEnabled && ownership.permits("delivery") && repository.ready();
        if (active && !listener.isRunning()) listener.start();
        if (!active && listener.isRunning()) listener.stop();
    }

    @RabbitListener(id = "delivery-module-consumer", queues = "${modulith.delivery.queue}", autoStartup = "false")
    void consume(String payload) {
        JsonNode message;
        try {
            message = mapper.readTree(payload);
        } catch (Exception invalid) {
            LOG.error("Invalid delivery JSON", invalid);
            return;
        }
        if (message == null || !message.hasNonNull("orderId")) {
            LOG.error("Delivery message missing orderId");
            return;
        }
        UUID orderId;
        try {
            orderId = UUID.fromString(message.get("orderId").asText());
        } catch (IllegalArgumentException invalid) {
            LOG.error("Delivery message has invalid orderId", invalid);
            return;
        }
        repository.save(orderId, optional(message, "foodName"),
                optional(message, "storeName"), optional(message, "stationName"));
    }

    private String optional(JsonNode message, String field) {
        return message.hasNonNull(field) ? message.get(field).asText() : null;
    }
}

@Configuration
@EnableRabbit
@EnableScheduling
@ConditionalOnProperty(name = "modulith.delivery.enabled", havingValue = "true")
class DeliveryQueueConfiguration {
    @Bean Queue deliveryQueue(@Value("${modulith.delivery.queue}") String name) {
        return new Queue(name, true);
    }
}
