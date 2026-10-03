package trainticket.preserveother.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.*;
import trainticket.preserveother.BookingRequest;
import trainticket.preserveother.PreserveOtherOperations;

@RestController
@ConditionalOnProperty(name="modulith.preserve-other.enabled", havingValue="true")
@RequestMapping("/api/v1/preserveotherservice")
class PreserveOtherController {
    private final PreserveOtherOperations preserve;
    PreserveOtherController(PreserveOtherOperations preserve) { this.preserve = preserve; }
    @GetMapping("/welcome") String welcome() { return "Welcome to [ PreserveOther Service ] !"; }
    @CrossOrigin(origins="*") @PostMapping("/preserveOther") Object book(
            @RequestBody BookingRequest request,
            @RequestHeader(value="Authorization", required=false) String authorization) {
        return preserve.book(request, authorization);
    }
}
