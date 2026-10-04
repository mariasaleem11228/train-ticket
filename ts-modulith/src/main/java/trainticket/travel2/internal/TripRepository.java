package trainticket.travel2.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Repository;
import trainticket.travel2.Trip;
import trainticket.travel2.TripId;
import trainticket.tripcatalog.TripCatalogOperations;
import trainticket.tripcatalog.TripSnapshot;

import java.util.List;

/** Travel2's API adapter; trip persistence belongs to Trip Catalog. */
@Repository("travel2TripRepository")
@ConditionalOnProperty(name="modulith.travel2.enabled",havingValue="true")
class TripRepository {
    private final TripCatalogOperations catalog;
    TripRepository(TripCatalogOperations catalog) { this.catalog=catalog; }
    Trip find(TripId id) { return from(catalog.find(id.toString(),false)); }
    List<Trip> all() { return catalog.all(false).stream().map(this::from).toList(); }
    List<Trip> byRoute(String routeId) {
        return catalog.byRoute(routeId,false).stream().map(this::from).toList();
    }
    void save(Trip trip) { catalog.save(snapshot(trip),false); }
    void delete(TripId id) { catalog.delete(id.toString(),false); }
    private Trip from(TripSnapshot row) {
        return row==null?null:new Trip(TripId.parse(row.tripId()),row.trainTypeId(),row.routeId(),
                row.startingTime(),row.startingStationId(),row.stationsId(),
                row.terminalStationId(),row.endTime());
    }
    private TripSnapshot snapshot(Trip trip) {
        return new TripSnapshot(trip.tripId().toString(),trip.trainTypeId(),trip.routeId(),
                trip.startingTime(),trip.startingStationId(),trip.stationsId(),
                trip.terminalStationId(),trip.endTime());
    }
}
