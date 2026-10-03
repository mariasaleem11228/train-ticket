package trainticket.ticketinfo;

import com.fasterxml.jackson.databind.JsonNode;
import trainticket.basic.BasicResult;
import trainticket.station.StationResult;

/** TicketInfo's published read-only contract. */
public interface TicketInfoOperations {
    StationResult stationId(String name);
    BasicResult travel(JsonNode query);
}
