package trainticket.travel;

import java.util.List;

/** Published Travel contract for future journey and booking modules. */
public interface TravelOperations {
    TravelResult<List<Trip>> all();
    TravelResult<Trip> find(String tripId);
    TravelResult<?> create(TravelInfo info);
    TravelResult<?> update(TravelInfo info);
    TravelResult<?> delete(String tripId);
    TravelResult<?> routes(List<String> routeIds);
    TravelResult<?> trainType(String tripId);
    TravelResult<?> route(String tripId);
    TravelResult<?> adminAll();
    TravelResult<?> search(TripQuery query);
    TravelResult<?> detail(TripDetailQuery query);
}
