package trainticket.adminbasic;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.*;
import trainticket.contacts.Contact;
import trainticket.contacts.ContactsOperations;
import trainticket.station.Station;
import trainticket.station.StationOperations;
import trainticket.train.TrainType;
import trainticket.train.TrainOperations;
import trainticket.config.Config;
import trainticket.config.ConfigOperations;
import trainticket.price.PriceConfig;
import trainticket.price.PriceOperations;
import java.util.UUID;

/** Administration facade over the five published catalogue APIs. */
@RestController
@RequestMapping("/api/v1/adminbasicservice")
@ConditionalOnProperty(name = "modulith.adminbasic.enabled", havingValue = "true")
class AdminBasicController {
    private final ContactsOperations contacts;
    private final StationOperations stations;
    private final TrainOperations trains;
    private final ConfigOperations configs;
    private final PriceOperations prices;

    AdminBasicController(ContactsOperations contacts, StationOperations stations,
                         TrainOperations trains, ConfigOperations configs, PriceOperations prices) {
        this.contacts = contacts;
        this.stations = stations;
        this.trains = trains;
        this.configs = configs;
        this.prices = prices;
    }

    @GetMapping("/welcome") String welcome() { return "Welcome to [ AdminBasicInfo Service ] !"; }

    @GetMapping("/adminbasic/contacts") Object contacts() { return contacts.all(); }
    @PostMapping("/adminbasic/contacts") Object createContact(@RequestBody Contact value) { return contacts.createAdmin(value); }
    @PutMapping("/adminbasic/contacts") Object updateContact(@RequestBody Contact value) { return contacts.modify(value); }
    @DeleteMapping("/adminbasic/contacts/{id}") Object deleteContact(@PathVariable String id) { return contacts.delete(id); }

    @GetMapping("/adminbasic/stations") Object stations() { return stations.list(); }
    @PostMapping("/adminbasic/stations") Object createStation(@RequestBody Station value) { return stations.create(value); }
    @PutMapping("/adminbasic/stations") Object updateStation(@RequestBody Station value) { return stations.update(value); }
    @DeleteMapping("/adminbasic/stations") Object deleteStation(@RequestBody Station value) { return stations.delete(value); }
    @DeleteMapping("/adminbasic/stations/{id}") Object deleteStationById(@PathVariable String id) { return stations.delete(new Station(id, "", 0)); }

    @GetMapping("/adminbasic/trains") Object trains() { return trains.all(); }
    @PostMapping("/adminbasic/trains") Object createTrain(@RequestBody TrainType value) { return trains.create(value); }
    @PutMapping("/adminbasic/trains") Object updateTrain(@RequestBody TrainType value) { return trains.update(value); }
    @DeleteMapping("/adminbasic/trains/{id}") Object deleteTrain(@PathVariable String id) { return trains.delete(id); }

    @GetMapping("/adminbasic/configs") Object configs() { return configs.all(); }
    @PostMapping("/adminbasic/configs") Object createConfig(@RequestBody Config value) { return configs.create(value); }
    @PutMapping("/adminbasic/configs") Object updateConfig(@RequestBody Config value) { return configs.update(value); }
    @DeleteMapping("/adminbasic/configs/{name}") Object deleteConfig(@PathVariable String name) { return configs.delete(name); }

    @GetMapping("/adminbasic/prices") Object prices() { return prices.all(); }
    @PostMapping("/adminbasic/prices") Object createPrice(@RequestBody PriceConfig value) { return prices.create(value); }
    @PutMapping("/adminbasic/prices") Object updatePrice(@RequestBody PriceConfig value) { return prices.update(value); }
    @DeleteMapping("/adminbasic/prices") Object deletePrice(@RequestBody PriceConfig value) { return prices.delete(value); }
    @DeleteMapping("/adminbasic/prices/{id}") Object deletePriceById(@PathVariable UUID id) {
        PriceConfig value = new PriceConfig();
        value.setId(id);
        return prices.delete(value);
    }
}
