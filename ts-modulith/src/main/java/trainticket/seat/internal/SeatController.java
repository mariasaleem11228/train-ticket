package trainticket.seat.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.*;
import trainticket.seat.SeatOperations;
import trainticket.seat.SeatRequest;

@RestController
@ConditionalOnProperty(name="modulith.seat.enabled", havingValue="true")
@RequestMapping("/api/v1/seatservice")
class SeatController {
    private final SeatOperations seats;
    SeatController(SeatOperations seats) { this.seats = seats; }
    @GetMapping("/welcome") String welcome() { return "Welcome to [ Seat Service ] !"; }
    @CrossOrigin(origins="*") @PostMapping("/seats") Object distribute(@RequestBody SeatRequest request) {
        return seats.distribute(request);
    }
    @CrossOrigin(origins="*") @PostMapping("/seats/left_tickets") Object left(@RequestBody SeatRequest request) {
        return seats.leftTickets(request);
    }
}
