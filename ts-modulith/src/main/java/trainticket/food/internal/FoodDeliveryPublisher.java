package trainticket.food.internal;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.amqp.core.Queue;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ResponseStatusException;
import trainticket.food.FoodOrder;
import trainticket.runtime.WriteOwnership;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;

@Component
@ConditionalOnProperty(name="modulith.food.enabled",havingValue="true")
class FoodDeliveryPublisher {
    private final RabbitTemplate rabbit;
    private final ObjectMapper mapper;
    private final String queue;
    private final WriteOwnership ownership;
    FoodDeliveryPublisher(RabbitTemplate rabbit,ObjectMapper mapper,
                          @Value("${modulith.food.delivery-queue}") String queue,
                          WriteOwnership ownership) {
        this.rabbit=rabbit;this.mapper=mapper;this.queue=queue;this.ownership=ownership;
    }
    void publish(FoodOrder order) {
        if (!ownership.permits("food"))
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,"Food delivery inactive");
        Map<String,Object> payload=new LinkedHashMap<>();
        payload.put("orderId",order.orderId());payload.put("foodName",order.foodName());
        payload.put("storeName",order.storeName());payload.put("stationName",order.stationName());
        try { rabbit.convertAndSend(queue,mapper.writeValueAsString(payload)); }
        catch (JsonProcessingException error) { throw new IllegalStateException(error); }
    }
    void testMessage() {
        publish(new FoodOrder(null,UUID.randomUUID(),2,"Shang Hai",
                "MiaoTing Instant-Boiled Mutton","HotPot",0));
    }
}

@Configuration
@ConditionalOnProperty(name="modulith.food.enabled",havingValue="true")
class FoodQueueConfiguration {
    @Bean Queue foodDeliveryQueue(@Value("${modulith.food.delivery-queue}") String name) {
        return new Queue(name,true);
    }
}
