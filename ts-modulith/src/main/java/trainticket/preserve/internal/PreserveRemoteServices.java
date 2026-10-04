package trainticket.preserve.internal;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;
import trainticket.assurance.AssuranceOperations;
import trainticket.consign.ConsignOperations;
import trainticket.consign.ConsignRequest;
import trainticket.food.FoodOperations;
import trainticket.food.FoodOrder;
import trainticket.ticketinfo.TicketInfoOperations;
import trainticket.user.UserOperations;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/** Booking collaborators exposed through their published module APIs. */
@Component
@ConditionalOnProperty(name="modulith.preserve.enabled", havingValue="true")
class PreserveRemoteServices {
    private final TicketInfoOperations ticketInfo;
    private final UserOperations users;
    private final AssuranceOperations assurances;
    private final FoodOperations foods;
    private final ConsignOperations consigns;
    private final ObjectMapper mapper;

    PreserveRemoteServices(TicketInfoOperations ticketInfo,UserOperations users,
                           AssuranceOperations assurances,FoodOperations foods,
                           ConsignOperations consigns,ObjectMapper mapper) {
        this.ticketInfo=ticketInfo;this.users=users;this.assurances=assurances;
        this.foods=foods;this.consigns=consigns;this.mapper=mapper;
    }
    JsonNode fares(Object trip,String from,String to,java.util.Date date,String auth) {
        Map<String,Object> query=Map.of("trip",trip,"startingPlace",from,"endPlace",to,"departureTime",date);
        return mapper.valueToTree(ticketInfo.travel(mapper.valueToTree(query)));
    }
    JsonNode user(String accountId,String auth) {
        return mapper.valueToTree(users.byId(UUID.fromString(accountId)));
    }
    JsonNode assurance(int type,String orderId,String auth) {
        return mapper.valueToTree(assurances.create(type,UUID.fromString(orderId)));
    }
    JsonNode food(Map<String,Object> order,String auth) {
        return mapper.valueToTree(foods.create(mapper.convertValue(order,FoodOrder.class)));
    }
    JsonNode consign(Map<String,Object> order,String auth) {
        Map<String,Object> body=new HashMap<>(order);
        body.put("isWithin",body.remove("within"));
        return mapper.valueToTree(consigns.create(mapper.convertValue(body,ConsignRequest.class)));
    }
}
