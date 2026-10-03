package trainticket.train.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.*;
import trainticket.train.TrainOperations;
import trainticket.train.TrainType;

@RestController
@ConditionalOnProperty(name="modulith.train.enabled", havingValue="true")
@RequestMapping("/api/v1/trainservice")
class TrainController {
    private final TrainOperations trains;
    TrainController(TrainOperations trains) { this.trains = trains; }
    @GetMapping("/trains/welcome") String welcome() { return "Welcome to [ Train Service ] !"; }
    @CrossOrigin(origins="*") @GetMapping("/trains") Object all() { return trains.all(); }
    @CrossOrigin(origins="*") @GetMapping("/trains/{id}") Object find(@PathVariable String id) { return trains.find(id); }
    @CrossOrigin(origins="*") @PostMapping("/trains") Object create(@RequestBody TrainType train) { return trains.create(train); }
    @CrossOrigin(origins="*") @PutMapping("/trains") Object update(@RequestBody TrainType train) { return trains.update(train); }
    @CrossOrigin(origins="*") @DeleteMapping("/trains/{id}") Object delete(@PathVariable String id) { return trains.delete(id); }
}
