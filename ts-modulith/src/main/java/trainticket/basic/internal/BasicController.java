package trainticket.basic.internal;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.HashMap;
import java.util.Map;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;
import trainticket.price.PriceConfig;
import trainticket.price.PriceOperations;
import trainticket.basic.BasicOperations;
import trainticket.basic.BasicResult;
import trainticket.basic.BasicTravelData;
import trainticket.route.Route;
import trainticket.route.RouteOperations;
import trainticket.station.StationOperations;
import trainticket.station.StationResult;
import trainticket.train.TrainOperations;
import trainticket.train.TrainType;

/** The deployed Basic service composes four catalogues and owns no data. */
@RestController
@ConditionalOnProperty(name = "modulith.basic.enabled", havingValue = "true")
@RequestMapping("/api/v1/basicservice")
class BasicController implements BasicOperations {
    private final StationOperations stations;
    private final TrainOperations trains;
    private final RouteOperations routes;
    private final PriceOperations prices;

    BasicController(StationOperations stations, TrainOperations trains,
                    RouteOperations routes, PriceOperations prices) {
        this.stations = stations;
        this.trains = trains;
        this.routes = routes;
        this.prices = prices;
    }

    @GetMapping("/welcome") String welcome() { return "Welcome to [ Basic Service ] !"; }

    @GetMapping("/basic/{stationName}") public StationResult stationId(@PathVariable String stationName) {
        StationResult result = stations.idForName(stationName);
        return result.getStatus() == 1 ? result : new StationResult(0, result.getMsg(), null);
    }

    @PostMapping("/basic/travel") public BasicResult travel(@RequestBody JsonNode info) {
        String start = text(info, "startingPlace");
        String end = text(info, "endPlace");
        JsonNode trip = info.path("trip");
        String trainId = text(trip, "trainTypeId");
        String routeId = text(trip, "routeId");

        int status = 1;
        String message = "Success";
        if (stations.idForName(start).getStatus() != 1 || stations.idForName(end).getStatus() != 1) {
            status = 0;
            message = "Start place or end place not exist!";
        }
        TrainType train = trains.find(trainId).data();
        if (train == null) {
            // The deployed Train lookup returns HTTP 404; legacy Basic turns that
            // downstream error into HTTP 500 rather than a normal Basic result.
            throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR);
        }
        Route route = routes.find(routeId).data();
        PriceConfig price = prices.find(routeId, train.getId()).data();
        String startId = (String) stationIdData(start);
        String endId = (String) stationIdData(end);
        int distance = 0;
        boolean distanceFailed = false;
        try {
            if (route != null) {
                int from = route.getStations().indexOf(startId);
                int to = route.getStations().indexOf(endId);
                distance = route.getDistances().get(to) - route.getDistances().get(from);
            }
        } catch (RuntimeException ignored) {
            distanceFailed = true;
        }
        Map<String, String> fare = new HashMap<>();
        if (price != null && !distanceFailed) {
            fare.put("economyClass", Double.toString(distance * price.getBasicPriceRate()));
            fare.put("confortClass", Double.toString(distance * price.getFirstClassPriceRate()));
        } else {
            fare.put("economyClass", "95.0");
            fare.put("confortClass", "120.0");
        }
        return new BasicResult(status, message, new BasicTravelData(status == 1,
                1.0, train, fare));
    }

    private Object stationIdData(String name) {
        StationResult found = stations.idForName(name);
        return found.getStatus() == 1 ? found.getData() : null;
    }

    private static String text(JsonNode node, String field) {
        JsonNode value = node.path(field);
        return value.isMissingNode() || value.isNull() ? null : value.asText();
    }

}
