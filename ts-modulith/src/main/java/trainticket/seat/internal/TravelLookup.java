package trainticket.seat.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Component;
import trainticket.route.Route;
import trainticket.route.RouteOperations;
import trainticket.train.TrainOperations;
import trainticket.train.TrainType;
import trainticket.tripcatalog.TripCatalogOperations;
import trainticket.tripcatalog.TripSnapshot;

import java.util.List;

/** Resolves seat-allocation metadata through published module APIs. */
@Component
@ConditionalOnProperty(name="modulith.seat.enabled", havingValue="true")
class TravelLookup {
    private final TripCatalogOperations trips;
    private final RouteOperations routes;
    private final TrainOperations trains;

    TravelLookup(TripCatalogOperations trips,RouteOperations routes,TrainOperations trains) {
        this.trips=trips;this.routes=routes;this.trains=trains;
    }
    List<String> stations(String number,boolean standard) {
        TripSnapshot trip=trip(number,standard);
        Route route=routes.find(trip.routeId()).data();
        if (route==null)throw new IllegalStateException("Route is unavailable for "+number);
        return route.getStations();
    }
    int capacity(String number,boolean standard,int seatType) {
        TripSnapshot trip=trip(number,standard);
        TrainType train=trains.find(trip.trainTypeId()).data();
        if (train==null)throw new IllegalStateException("Train type is unavailable for "+number);
        return seatType==2?train.getConfortClass():train.getEconomyClass();
    }
    private TripSnapshot trip(String number,boolean standard) {
        TripSnapshot trip=trips.find(number,standard);
        if (trip==null)throw new IllegalStateException("Trip is unavailable for "+number);
        return trip;
    }
}
