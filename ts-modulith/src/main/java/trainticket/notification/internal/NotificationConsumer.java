package trainticket.notification.internal;

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
import trainticket.notification.NotifyInfo;
import trainticket.runtime.WriteOwnership;
import java.util.UUID;

@Component
@ConditionalOnProperty(name="modulith.notification.enabled",havingValue="true")
class NotificationConsumer {
    private static final Logger LOG=LoggerFactory.getLogger(NotificationConsumer.class);
    private final ObjectMapper mapper;
    private final NotificationEmailService email;
    private final NotificationRepository repository;
    private final RabbitListenerEndpointRegistry registry;
    private final WriteOwnership ownership;
    private final boolean writesEnabled;
    NotificationConsumer(ObjectMapper mapper,NotificationEmailService email,
                         NotificationRepository repository,RabbitListenerEndpointRegistry registry,
                         WriteOwnership ownership,
                         @Value("${modulith.notification.writes-enabled:false}") boolean writesEnabled) {
        this.mapper=mapper;this.email=email;this.repository=repository;
        this.registry=registry;this.ownership=ownership;this.writesEnabled=writesEnabled;
    }
    @Scheduled(fixedDelay=1000)
    void updateConsumerOwnership() {
        MessageListenerContainer listener=registry.getListenerContainer("notification-module-consumer");
        if (listener==null)return;
        boolean active=writesEnabled && ownership.permits("notification");
        if (active && !listener.isRunning())listener.start();
        if (!active && listener.isRunning())listener.stop();
    }
    @RabbitListener(id="notification-module-consumer",queues="${modulith.notification.queue}",autoStartup="false")
    void consume(String payload) {
        NotifyInfo info;
        try { info=mapper.readValue(payload,NotifyInfo.class); }
        catch (Exception error) { LOG.error("Invalid notification message",error);return; }
        if (info==null)return;
        boolean sent=email.send("preserve",info);
        repository.save(info.delivered(UUID.randomUUID(),sent));
    }
}

@Configuration
@EnableRabbit
@EnableScheduling
@ConditionalOnProperty(name="modulith.notification.enabled",havingValue="true")
class NotificationQueueConfiguration {
    @Bean Queue notificationQueue(@Value("${modulith.notification.queue}") String name) {
        return new Queue(name,true);
    }
}
