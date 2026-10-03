package trainticket.station.internal;

import trainticket.station.Station;
import java.util.List;

interface StationStore {
    Station findById(String id);
    Station findByName(String name);
    List<Station> findAll();
    void save(Station station);
    void delete(String id);
}
