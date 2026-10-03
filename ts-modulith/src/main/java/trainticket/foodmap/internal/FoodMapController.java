package trainticket.foodmap.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.*;
import trainticket.foodmap.FoodMapOperations;

import java.util.List;
import java.util.Map;

@RestController
@ConditionalOnProperty(name="modulith.foodmap.enabled",havingValue="true")
@RequestMapping("/api/v1/foodmapservice")
class FoodMapController {
    private final FoodMapRepository repository;
    private final FoodMapOperations operations;
    FoodMapController(FoodMapRepository repository,FoodMapOperations operations) {
        this.repository=repository;this.operations=operations;
    }
    record Result(int status,String msg,Object data) {}
    private Result listed(List<Map<String,Object>> rows,String empty) {
        return rows.isEmpty()?new Result(0,empty,null):new Result(1,"Success",rows);
    }
    @GetMapping("/trainfoods/welcome") String trainWelcome() { return "Welcome to [ Train Food Service ] !"; }
    @GetMapping("/foodstores/welcome") String storeWelcome() { return "Welcome to [ Food store Service ] !"; }
    @GetMapping("/trainfoods") Result trains() { return listed(repository.trains(),"No content"); }
    @GetMapping("/trainfoods/{tripId}") Result trains(@PathVariable String tripId) {
        return new Result(1,"Success",operations.trainFoods(tripId));
    }
    @GetMapping("/foodstores") Result stores() { return listed(repository.stores(),"Food store is empty"); }
    @GetMapping("/foodstores/{stationId}") Result stores(@PathVariable String stationId) {
        return listed(repository.stores(stationId),"Food store is empty");
    }
    @PostMapping("/foodstores") Result stores(@RequestBody List<String> stationIds) {
        return new Result(1,"Success",operations.stores(stationIds));
    }
}
