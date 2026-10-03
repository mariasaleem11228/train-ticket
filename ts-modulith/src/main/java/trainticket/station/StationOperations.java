package trainticket.station;

import java.util.List;

/** Only this API and its DTOs are available to other modules. */
public interface StationOperations {
    StationResult list();
    StationResult create(Station station);
    StationResult update(Station station);
    StationResult delete(Station station);
    StationResult idForName(String name);
    StationResult idsForNames(List<String> names);
    StationResult nameForId(String id);
    StationResult namesForIds(List<String> ids);
}
