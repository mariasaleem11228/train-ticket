package trainticket.ticketinfo.internal;

import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.*;
import trainticket.basic.BasicOperations;
import trainticket.basic.BasicResult;
import trainticket.station.StationResult;
import trainticket.ticketinfo.TicketInfoOperations;

@RestController
@ConditionalOnProperty(name="modulith.ticketinfo.enabled",havingValue="true")
@RequestMapping("/api/v1/ticketinfoservice")
class TicketInfoController implements TicketInfoOperations {
    private final BasicOperations basic;
    TicketInfoController(BasicOperations basic) { this.basic=basic; }

    @GetMapping("/welcome") String welcome() { return "Welcome to [ TicketInfo Service ] !"; }
    @GetMapping("/ticketinfo/{name}") public StationResult stationId(@PathVariable String name) {
        return basic.stationId(name);
    }
    @PostMapping("/ticketinfo") public BasicResult travel(@RequestBody JsonNode query) {
        return basic.travel(query);
    }
}
