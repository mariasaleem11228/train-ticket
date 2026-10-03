package trainticket.consign;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.UUID;

public record ConsignRequest(UUID id, UUID orderId, UUID accountId, String handleDate,
                             String targetDate, String from, String to, String consignee,
                             String phone, double weight, @JsonProperty("isWithin") boolean isWithin) { }
