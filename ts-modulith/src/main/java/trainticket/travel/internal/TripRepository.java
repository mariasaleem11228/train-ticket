package trainticket.travel.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Repository;
import trainticket.travel.Trip;
import trainticket.travel.TripId;
import trainticket.tripcatalog.TripCatalogOperations;
import trainticket.tripcatalog.TripSnapshot;

import java.util.List;

/** Travel's API adapter; trip persistence belongs to Trip Catalog. */
@Repository
@ConditionalOnProperty(name="modulith.travel.enabled",havingValue="true")
class TripRepository {
    private final TripCatalogOperations catalog;
    TripRepository(TripCatalogOperations catalog) { this.catalog=catalog; }
    Trip find(TripId id) { return from(catalog.find(id.toString(),true)); }
    List<Trip> all() { return catalog.all(true).stream().map(this::from).toList(); }
    List<Trip> byRoute(String routeId) {
        return catalog.byRoute(routeId,true).stream().map(this::from).toList();
    }
    void save(Trip trip) { catalog.save(snapshot(trip),true); }
    void delete(TripId id) { catalog.delete(id.toString(),true); }
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
