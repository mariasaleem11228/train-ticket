package trainticket.preserve.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.*;
import trainticket.preserve.BookingRequest;
import trainticket.preserve.PreserveOperations;

@RestController
@ConditionalOnProperty(name="modulith.preserve.enabled", havingValue="true")
@RequestMapping("/api/v1/preserveservice")
class PreserveController {
    private final PreserveOperations preserve;
    PreserveController(PreserveOperations preserve) { this.preserve = preserve; }
    @GetMapping("/welcome") String welcome() { return "Welcome to [ Preserve Service ] !"; }
    @CrossOrigin(origins="*") @PostMapping("/preserve") Object book(
            @RequestBody BookingRequest request,
            @RequestHeader(value="Authorization", required=false) String authorization) {
        return preserve.book(request, authorization);
    }
}
