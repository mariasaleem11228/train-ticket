package trainticket.station.internal;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import trainticket.station.*;
import java.util.List;

@RestController
@RequestMapping("/api/v1/stationservice")
class StationController {
    private final StationOperations stations;
    StationController(StationOperations stations) { this.stations = stations; }
    @GetMapping("/welcome") public String welcome() { return "Welcome to [ Station Service ] !"; }
    @GetMapping("/stations") public StationResult list() { return stations.list(); }
    @PostMapping("/stations") public ResponseEntity<StationResult> create(@RequestBody Station station) {
        return ResponseEntity.status(201).body(stations.create(station));
    }
    @PutMapping("/stations") public StationResult update(@RequestBody Station station) { return stations.update(station); }
    // Running 0.2.0 callers send DELETE with a JSON body, not a path ID.
    @DeleteMapping("/stations") public StationResult delete(@RequestBody Station station) { return stations.delete(station); }
    @GetMapping("/stations/id/{name}") public StationResult id(@PathVariable String name) { return stations.idForName(name); }
    @PostMapping("/stations/idlist") @CrossOrigin(origins = "*")
    public StationResult ids(@RequestBody List<String> names) { return stations.idsForNames(names); }
    @GetMapping("/stations/name/{id}") @CrossOrigin(origins = "*")
    public StationResult name(@PathVariable String id) { return stations.nameForId(id); }
    @PostMapping("/stations/namelist") @CrossOrigin(origins = "*")
    public StationResult names(@RequestBody List<String> ids) { return stations.namesForIds(ids); }
}
