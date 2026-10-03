package trainticket.admintravel;

import java.util.ArrayList;
import java.util.List;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.*;
import trainticket.travel.TravelInfo;

/** Admin facade over the two published journey APIs. */
@RestController
@RequestMapping("/api/v1/admintravelservice")
@ConditionalOnProperty(name = "modulith.admintravel.enabled", havingValue = "true")
class AdminTravelController {
    private final trainticket.travel.TravelOperations travel;
    private final trainticket.travel2.TravelOperations travel2;

    AdminTravelController(trainticket.travel.TravelOperations travel,
                          trainticket.travel2.TravelOperations travel2) {
        this.travel = travel;
        this.travel2 = travel2;
    }

    record Response(int status, String msg, Object data) { }

    @GetMapping("/welcome") String welcome() { return "Welcome to [ AdminTravel Service ] !"; }

    @GetMapping("/admintravel") Response all() {
        var first = travel.adminAll();
        var second = travel2.adminAll();
        List<Object> trips = new ArrayList<>();
        if (first.status() == 1 && first.data() instanceof List<?> list) trips.addAll(list);
        if (second.status() == 1 && second.data() instanceof List<?> list) trips.addAll(list);
        return new Response(second.status(), second.msg(), trips);
    }

    @PostMapping("/admintravel") Response create(@RequestBody TravelInfo info) {
        Response result = write(info, false);
        return result.status() == 1 ? new Response(1, "[Admin add new travel]", null)
                : new Response(0, "Admin add new travel failed", null);
    }

    @PutMapping("/admintravel") Response update(@RequestBody TravelInfo info) {
        Response result = write(info, true);
        return result.status() == 1 ? result : new Response(0, "Admin update travel failed", null);
    }

    @DeleteMapping("/admintravel/{tripId}") Response delete(@PathVariable String tripId) {
        Response result = fast(tripId) ? from(travel.delete(tripId)) : from(travel2.delete(tripId));
        return result.status() == 1 ? result : new Response(0, "Admin delete travel failed", null);
    }

    private Response write(TravelInfo info, boolean update) {
        if (fast(info.trainTypeId()))
            return from(update ? travel.update(info) : travel.create(info));
        var other = new trainticket.travel2.TravelInfo(info.tripId(), info.trainTypeId(), info.routeId(),
                info.startingStationId(), info.stationsId(), info.terminalStationId(),
                info.startingTime(), info.endTime());
        return from(update ? travel2.update(other) : travel2.create(other));
    }

    private boolean fast(String id) { return id.charAt(0) == 'G' || id.charAt(0) == 'D'; }
    private Response from(trainticket.travel.TravelResult<?> value) {
        return new Response(value.status(), value.msg(), value.data());
    }
    private Response from(trainticket.travel2.TravelResult<?> value) {
        return new Response(value.status(), value.msg(), value.data());
    }
}
