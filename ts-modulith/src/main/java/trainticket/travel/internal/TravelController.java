package trainticket.travel.internal;

import java.util.List;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import trainticket.travel.*;

@RestController
@ConditionalOnProperty(name="modulith.travel.enabled",havingValue="true")
@RequestMapping("/api/v1/travelservice")
class TravelController {
    private final TravelOperations travel;
    TravelController(TravelOperations travel) { this.travel=travel; }
    @GetMapping("/welcome") String welcome() { return "Welcome to [ Travel Service ] !"; }
    @GetMapping("/train_types/{tripId}") Object train(@PathVariable String tripId) { return travel.trainType(tripId); }
    @GetMapping("/routes/{tripId}") Object route(@PathVariable String tripId) { return travel.route(tripId); }
    @PostMapping("/trips/routes") Object routes(@RequestBody List<String> ids) { return travel.routes(ids); }
    @PostMapping("/trips") ResponseEntity<?> create(@RequestBody TravelInfo info) {
        return ResponseEntity.status(201).body(travel.create(info));
    }
    @GetMapping("/trips/{tripId}") Object find(@PathVariable String tripId) { return travel.find(tripId); }
    @PutMapping("/trips") Object update(@RequestBody TravelInfo info) { return travel.update(info); }
    @DeleteMapping("/trips/{tripId}") Object delete(@PathVariable String tripId) { return travel.delete(tripId); }
    @PostMapping("/trips/left") Object search(@RequestBody TripQuery query) {
        if(query.startingPlace()==null || query.startingPlace().isEmpty() ||
                query.endPlace()==null || query.endPlace().isEmpty() || query.departureTime()==null)
            return List.of();
        return travel.search(query);
    }
    @PostMapping("/trip_detail") Object detail(@RequestBody TripDetailQuery query) { return travel.detail(query); }
    @GetMapping("/trips") Object all() { return travel.all(); }
    @GetMapping("/admin_trip") Object adminAll() { return travel.adminAll(); }
}
