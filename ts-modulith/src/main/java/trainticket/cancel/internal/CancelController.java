package trainticket.cancel.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;
import trainticket.cancel.*;

@RestController
@RequestMapping("/api/v1/cancelservice")
@ConditionalOnProperty(name="modulith.cancel.enabled",havingValue="true")
class CancelController {
    private final CancelOperations service;
    CancelController(CancelOperations service) { this.service=service; }
    @GetMapping("/welcome") String welcome() { return "Welcome to [ Cancel Service ] !"; }
    @GetMapping("/cancel/refound/{orderId}") CancelResult<?> refund(@PathVariable String orderId) {
        return service.refund(orderId);
    }
    @GetMapping("/cancel/{orderId}/{loginId}") CancelResult<?> cancel(
            @PathVariable String orderId,@PathVariable String loginId,
            @RequestHeader(value="Authorization",required=false) String authorization) {
        try { return service.cancel(orderId,loginId,authorization); }
        catch(ResponseStatusException ex) {
            if(ex.getStatusCode()==HttpStatus.SERVICE_UNAVAILABLE)throw ex;
            return new CancelResult<>(1,"error",null);
        }
        catch(Exception ex) { return new CancelResult<>(1,"error",null); }
    }
}
