package trainticket.tripcatalog;

import java.util.List;

/** The sole owner of the two legacy trip collections. */
public interface TripCatalogOperations {
    TripSnapshot find(String tripId, boolean standard);
    List<TripSnapshot> all(boolean standard);
    List<TripSnapshot> byRoute(String routeId, boolean standard);
    void save(TripSnapshot trip, boolean standard);
    void delete(String tripId, boolean standard);
}
