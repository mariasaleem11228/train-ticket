package trainticket.rebook.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.*;
import trainticket.rebook.RebookInfo;
import trainticket.rebook.RebookOperations;
import trainticket.rebook.RebookResult;

@RestController
@RequestMapping("/api/v1/rebookservice")
@ConditionalOnProperty(name="modulith.rebook.enabled",havingValue="true")
class RebookController {
    private final RebookOperations service;
    RebookController(RebookOperations service){this.service=service;}
    @GetMapping("/welcome") String welcome(){return "Welcome to [ Rebook Service ] !";}
    @PostMapping("/rebook") RebookResult<?> rebook(@RequestBody RebookInfo info){return service.rebook(info);}
    @PostMapping("/rebook/difference") RebookResult<?> difference(@RequestBody RebookInfo info){return service.payDifference(info);}
}
