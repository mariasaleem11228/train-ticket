package trainticket.station.internal;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;
import trainticket.station.*;
import java.util.ArrayList;
import java.util.List;

/** Ports Station behaviour, retaining the running Mongo release's wire contract. */
@Service
class StationService implements StationOperations {
    @org.springframework.beans.factory.annotation.Autowired(required=false)
    private trainticket.runtime.WriteOwnership ownership;
    private final StationStore store;
    private final boolean writesEnabled;
    StationService(StationStore store, @Value("${modulith.station.writes-enabled:false}") boolean writesEnabled) {
        this.store = store; this.writesEnabled = writesEnabled;
    }
    private void requireWriter() {
        if (!writesEnabled || (ownership != null && !ownership.permits("station")))
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "Station writes disabled");
    }
    public StationResult list() {
        List<Station> stations = store.findAll();
        return stations.isEmpty() ? new StationResult(0, "No content", null)
                : new StationResult(1, "Find all content", stations);
    }
    public StationResult create(Station station) {
        requireWriter();
        if (store.findById(station.getId()) != null) return new StationResult(0, "Already exists", station);
        store.save(station);
        return new StationResult(1, "Create success", station);
    }
    public StationResult update(Station station) {
        requireWriter();
        if (store.findById(station.getId()) == null) return new StationResult(0, "Station not exist", null);
        store.save(station);
        return new StationResult(1, "Update success", station);
    }
    public StationResult delete(Station request) {
        requireWriter();
        String id = request.getId();
        Station station = store.findById(id);
        if (station == null) return new StationResult(0, "Station not exist", null);
        store.delete(id);
        // Legacy deletion returns the submitted ID/name and a zero stayTime.
        return new StationResult(1, "Delete success", new Station(id, request.getName(), 0));
    }
    public StationResult idForName(String name) {
        Station station = store.findByName(name);
        return station == null ? new StationResult(0, "Not exists", name) : new StationResult(1, "Success", station.getId());
    }
    public StationResult idsForNames(List<String> names) {
        List<String> result = new ArrayList<>();
        for (String name : names) {
            Station station = store.findByName(name);
            result.add(station == null ? "Not Exist" : station.getId());
        }
        return result.isEmpty() ? new StationResult(0, "No content according to name list", null)
                : new StationResult(1, "Success", result);
    }
    public StationResult nameForId(String id) {
        Station station = store.findById(id);
        return station == null ? new StationResult(0, "No that stationId", id) : new StationResult(1, "Success", station.getName());
    }
    public StationResult namesForIds(List<String> ids) {
        List<String> result = new ArrayList<>();
        for (String id : ids) {
            Station station = store.findById(id);
            if (station != null) result.add(station.getName());
        }
        return result.isEmpty() ? new StationResult(0, "No stationNamelist according to stationIdList", result)
                : new StationResult(1, "Success", result);
    }
}
