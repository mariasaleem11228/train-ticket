package trainticket.basic;

import com.fasterxml.jackson.databind.JsonNode;
import trainticket.station.StationResult;

/** Published Basic contract used by TicketInfo without an HTTP call. */
public interface BasicOperations {
    StationResult stationId(String name);
    BasicResult travel(JsonNode query);
}
