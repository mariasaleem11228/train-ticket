package trainticket.preserveother.internal;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;
import trainticket.ticketinfo.TicketInfoOperations;
import java.util.Map;

/** HTTP remains only for services outside the shared host. */
@Component
@ConditionalOnProperty(name="modulith.preserve-other.enabled", havingValue="true")
class PreserveOtherRemoteServices {
    private final RestTemplate http;
    private final String ticketInfoUrl, userUrl, assuranceUrl, foodUrl, consignUrl;
    private final ObjectProvider<TicketInfoOperations> ticketInfo;
    private final ObjectMapper mapper;
    PreserveOtherRemoteServices(
            @Value("${modulith.preserve-other.ticket-info-url}") String ticketInfoUrl,
            @Value("${modulith.preserve-other.user-url}") String userUrl,
            @Value("${modulith.preserve-other.assurance-url}") String assuranceUrl,
            @Value("${modulith.preserve-other.food-url}") String foodUrl,
            @Value("${modulith.preserve-other.consign-url}") String consignUrl,
            ObjectProvider<TicketInfoOperations> ticketInfo,ObjectMapper mapper) {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(5000);
        factory.setReadTimeout(20000);
        http = new RestTemplate(factory);
        this.ticketInfoUrl=ticketInfoUrl; this.userUrl=userUrl;
        this.assuranceUrl=assuranceUrl; this.foodUrl=foodUrl; this.consignUrl=consignUrl;
        this.ticketInfo=ticketInfo;this.mapper=mapper;
    }
    JsonNode fares(Object trip, String from, String to, java.util.Date date, String auth) {
        Map<String,Object> query=Map.of("trip",trip,"startingPlace",from,"endPlace",to,"departureTime",date);
        TicketInfoOperations local=ticketInfo.getIfAvailable();
        return local==null?post(ticketInfoUrl+"/api/v1/ticketinfoservice/ticketinfo",query,auth):
                mapper.valueToTree(local.travel(mapper.valueToTree(query)));
    }
    JsonNode user(String accountId, String auth) {
        return get(userUrl + "/api/v1/userservice/users/id/" + accountId, auth);
    }
    JsonNode assurance(int type, String orderId, String auth) {
        return get(assuranceUrl + "/api/v1/assuranceservice/assurances/" + type + "/" + orderId, auth);
    }
    JsonNode food(Map<String,Object> order, String auth) {
        return post(foodUrl + "/api/v1/foodservice/orders", order, auth);
    }
    JsonNode consign(Map<String,Object> order, String auth) {
        return post(consignUrl + "/api/v1/consignservice/consigns", order, auth);
    }
    private JsonNode get(String url, String auth) {
        return http.exchange(url, HttpMethod.GET, new HttpEntity<>(headers(auth)), JsonNode.class).getBody();
    }
    private JsonNode post(String url, Object body, String auth) {
        return http.exchange(url, HttpMethod.POST, new HttpEntity<>(body, headers(auth)), JsonNode.class).getBody();
    }
    private HttpHeaders headers(String auth) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        if (auth != null) headers.set("Authorization", auth);
        return headers;
    }
}
