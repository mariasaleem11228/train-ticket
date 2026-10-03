package trainticket.seat.internal;

import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;

/** Travel and Travel2 stay remote until their later migration stages. */
@Component
@ConditionalOnProperty(name="modulith.seat.enabled", havingValue="true")
class TravelLookup {
    private final RestTemplate http;
    private final String travel;
    private final String travel2;

    TravelLookup(@Value("${modulith.seat.travel-url:http://ts-travel-service:12346}") String travel,
                 @Value("${modulith.seat.travel2-url:http://ts-travel2-service:16346}") String travel2) {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(Duration.ofSeconds(5));
        factory.setReadTimeout(Duration.ofSeconds(20));
        http = new RestTemplate(factory);
        this.travel = travel;
        this.travel2 = travel2;
    }
    List<String> stations(String number, boolean standard) {
        JsonNode node = data(number, standard, "routes").path("stations");
        List<String> result = new ArrayList<>();
        node.forEach(item -> result.add(item.asText()));
        return result;
    }
    int capacity(String number, boolean standard, int seatType) {
        JsonNode node = data(number, standard, "train_types");
        return node.path(seatType == 2 ? "confortClass" : "economyClass").asInt();
    }
    private JsonNode data(String number, boolean standard, String resource) {
        String base = standard ? travel + "/api/v1/travelservice/" : travel2 + "/api/v1/travel2service/";
        JsonNode response = http.getForObject(base + resource + "/" + number, JsonNode.class);
        if (response == null || response.path("data").isNull() || response.path("data").isMissingNode())
            throw new IllegalStateException("Travel " + resource + " is unavailable for " + number);
        return response.path("data");
    }
}
