package trainticket.preserveother.internal;

import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;
import trainticket.contacts.Contact;
import trainticket.contacts.ContactResult;
import trainticket.contacts.ContactsOperations;
import trainticket.orderother.Order;
import trainticket.orderother.OrderOtherOperations;
import trainticket.orderother.OrderOtherResult;
import trainticket.orderother.OrderStatus;
import trainticket.preserveother.BookingRequest;
import trainticket.preserveother.BookingResult;
import trainticket.preserveother.PreserveOtherOperations;
import trainticket.runtime.WriteOwnership;
import trainticket.seat.SeatOperations;
import trainticket.seat.SeatRequest;
import trainticket.seat.SeatResult;
import trainticket.seat.SeatTicket;
import trainticket.security.SecurityOperations;
import trainticket.security.SecurityResult;
import trainticket.station.StationOperations;
import trainticket.station.StationResult;
import trainticket.travel2.TravelOperations;
import trainticket.travel2.TravelResult;
import trainticket.travel2.Trip;
import trainticket.travel2.TripDetailQuery;
import trainticket.travel2.TripResponse;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/** Coordinates booking through published module APIs and remote ancillary services. */
@Service
@ConditionalOnProperty(name="modulith.preserve-other.enabled", havingValue="true")
class PreserveOtherApplicationService implements PreserveOtherOperations {
    private final SecurityOperations security;
    private final ContactsOperations contacts;
    private final TravelOperations travel;
    private final StationOperations stations;
    private final SeatOperations seats;
    private final OrderOtherOperations orders;
    private final PreserveOtherRemoteServices remote;
    private final WriteOwnership ownership;
    private final boolean writesEnabled;

    PreserveOtherApplicationService(SecurityOperations security, ContactsOperations contacts,
                               TravelOperations travel, StationOperations stations,
                               SeatOperations seats, OrderOtherOperations orders,
                               PreserveOtherRemoteServices remote, WriteOwnership ownership,
                               @Value("${modulith.preserve-other.writes-enabled:false}") boolean writesEnabled) {
        this.security=security; this.contacts=contacts; this.travel=travel;
        this.stations=stations; this.seats=seats; this.orders=orders;
        this.remote=remote; this.ownership=ownership; this.writesEnabled=writesEnabled;
    }

    @Override public BookingResult book(BookingRequest request, String authorization) {
        // A disabled candidate must not reach order, insurance, food or consign writes.
        if (!writesEnabled || !ownership.permits("preserveother"))
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "PreserveOther writes disabled");

        SecurityResult<String> policy = security.check(request.accountId());
        if (policy.status() == 0) return failure(policy.msg());
        ContactResult<Contact> found = contacts.byId(request.contactsId());
        if (found.status() == 0) return failure(found.msg());
        Contact contact = found.data();

        TravelResult<?> journey = travel.detail(new TripDetailQuery(request.tripId(), request.date(),
                request.from(), request.to()));
        if (journey.status() == 0) return failure(journey.msg());
        Map<?,?> detail = (Map<?,?>) journey.data();
        TripResponse tripResponse = (TripResponse) detail.get("tripResponse");
        Trip trip = (Trip) detail.get("trip");
        if (tripResponse == null || trip == null) return failure("No Trip info content");
        if (request.seatType() == 2 && tripResponse.confortClass() == 0)
            return failure("Seat Not Enough");
        if (request.seatType() != 2 && tripResponse.economyClass() == 3
                && tripResponse.confortClass() == 0) return failure("Check Seat Not Enough");

        String fromId = stationId(request.from());
        String toId = stationId(request.to());
        JsonNode fares = remote.fares(trip, request.from(), request.to(), new java.util.Date(), authorization)
                .path("data").path("prices");
        SeatRequest seat = new SeatRequest();
        seat.setTravelDate(request.date()); seat.setTrainNumber(request.tripId());
        seat.setStartStation(fromId); seat.setDestStation(toId); seat.setSeatType(request.seatType());
        SeatResult<SeatTicket> allocation = seats.distribute(seat);
        if (allocation.status() == 0 || allocation.data() == null) return failure("Seat Not Enough");

        Order order = new Order();
        order.setId(UUID.randomUUID());
        order.setTrainNumber(request.tripId());
        order.setAccountId(UUID.fromString(request.accountId()));
        order.setFrom(fromId); order.setTo(toId);
        order.setBoughtDate(new java.util.Date());
        order.setStatus(OrderStatus.NOTPAID.getCode());
        order.setContactsDocumentNumber(contact.documentNumber());
        order.setContactsName(contact.name());
        order.setDocumentType(contact.documentType());
        order.setSeatClass(request.seatType() == 2 ? 2 : 3);
        order.setTravelDate(request.date());
        order.setTravelTime(tripResponse.startingTime());
        order.setSeatNumber(Integer.toString(allocation.data().seatNo()));
        order.setPrice(fares.path(request.seatType() == 2 ? "confortClass" : "economyClass").asText());
        OrderOtherResult<?> created = orders.create(order);
        if (created.getStatus() == 0) return failure(created.getMsg());
        Order saved = (Order) created.getData();
        String message = "Success.";

        if (request.assurance() != 0) {
            JsonNode result = remote.assurance(request.assurance(), saved.getId().toString(), authorization);
            if (result.path("status").asInt() != 1) message = "Success.But Buy Assurance Fail.";
        }
        if (request.foodType() != 0) {
            Map<String,Object> food = new HashMap<>();
            food.put("orderId", saved.getId()); food.put("foodType", request.foodType());
            food.put("foodName", request.foodName()); food.put("price", request.foodPrice());
            if (request.foodType() == 2) {
                food.put("stationName", request.stationName()); food.put("storeName", request.storeName());
            }
            JsonNode result = remote.food(food, authorization);
            if (result.path("status").asInt() != 1) message = "Success.But Buy Food Fail.";
        }
        if (request.consigneeName() != null && !request.consigneeName().isEmpty()) {
            Map<String,Object> consign = new HashMap<>();
            consign.put("orderId", saved.getId()); consign.put("accountId", saved.getAccountId());
            consign.put("handleDate", request.handleDate());
            consign.put("targetDate", saved.getTravelDate().toString());
            consign.put("from", saved.getFrom()); consign.put("to", saved.getTo());
            consign.put("consignee", request.consigneeName());
            consign.put("phone", request.consigneePhone());
            consign.put("weight", request.consigneeWeight());
            consign.put("within", request.isWithin());
            JsonNode result = remote.consign(consign, authorization);
            if (result.path("status").asInt() != 1) message = "Consign Fail.";
        }
        // The deployed image looks up the user but does not publish its composed notification.
        remote.user(saved.getAccountId().toString(), authorization);
        return new BookingResult(1, message, created.getMsg());
    }
    private String stationId(String name) {
        StationResult found = stations.idForName(name);
        return found.getStatus() == 1 ? (String) found.getData() : null;
    }
    private BookingResult failure(String message) { return new BookingResult(0, message, null); }
}
