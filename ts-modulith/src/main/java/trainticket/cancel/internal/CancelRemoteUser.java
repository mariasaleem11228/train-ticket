package trainticket.cancel.internal;

import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

/** User remains outside the shared host; cancellation notifications remain disabled. */
@Component
@ConditionalOnProperty(name="modulith.cancel.enabled",havingValue="true")
class CancelRemoteUser {
    private final RestTemplate http;
    private final String url;
    CancelRemoteUser(@Value("${modulith.cancel.user-url}") String url) {
        SimpleClientHttpRequestFactory factory=new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(5000);factory.setReadTimeout(20000);
        http=new RestTemplate(factory);this.url=url;
    }
    JsonNode get(String accountId,String authorization) {
        HttpHeaders headers=new HttpHeaders();
        if(authorization!=null)headers.set("Authorization",authorization);
        return http.exchange(url+"/api/v1/userservice/users/id/"+accountId,
                HttpMethod.GET,new HttpEntity<>(headers),JsonNode.class).getBody();
    }
}
