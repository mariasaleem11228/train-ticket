package trainticket.ticketoffice;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.core.JsonProcessingException;
import java.io.IOException;
import java.util.List;
import java.util.Map;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.core.io.ClassPathResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/office")
@ConditionalOnProperty(name = "modulith.ticketoffice.enabled", havingValue = "true")
class TicketOfficeController {
    private final TicketOfficeRepository offices;
    private final ObjectMapper mapper;
    private final JsonNode regions;

    TicketOfficeController(TicketOfficeRepository offices, ObjectMapper mapper) throws IOException {
        this.offices = offices;
        this.mapper = mapper;
        try (var input = new ClassPathResource("ticket-office-region.json").getInputStream()) {
            regions = mapper.readTree(input);
        }
    }

    @GetMapping({"", "/"})
    ResponseEntity<String> welcome() {
        return ResponseEntity.ok().header(HttpHeaders.CONTENT_TYPE, "text/html; charset=utf-8")
                .body("welcome to ts-ticket-office-service");
    }

    @GetMapping("/getRegionList")
    ResponseEntity<JsonNode> regions() {
        return ResponseEntity.ok().header(HttpHeaders.CONTENT_TYPE, "application/json; charset=utf-8").body(regions);
    }

    @GetMapping("/getAll")
    ResponseEntity<String> all() throws JsonProcessingException { return databaseResponse(offices.all()); }

    @PostMapping("/getSpecificOffices")
    ResponseEntity<String> specific(@RequestBody Map<String,Object> request) throws JsonProcessingException {
        return databaseResponse(offices.specific(str(request,"province"), str(request,"city"), str(request,"region")));
    }

    @PostMapping("/addOffice")
    ResponseEntity<String> add(@RequestBody Map<String,Object> request) throws JsonProcessingException {
        return databaseResponse(offices.add(str(request,"province"), str(request,"city"), str(request,"region"), office(request,"office")));
    }

    @PostMapping("/deleteOffice")
    ResponseEntity<String> delete(@RequestBody Map<String,Object> request) throws JsonProcessingException {
        return databaseResponse(offices.delete(str(request,"province"), str(request,"city"), str(request,"region"), str(request,"officeName")));
    }

    @PostMapping("/updateOffice")
    ResponseEntity<String> update(@RequestBody Map<String,Object> request) throws JsonProcessingException {
        return databaseResponse(offices.update(str(request,"province"), str(request,"city"), str(request,"region"),
                str(request,"oldOfficeName"), office(request,"newOffice")));
    }

    private ResponseEntity<String> databaseResponse(Object body) throws JsonProcessingException {
        return ResponseEntity.ok().header(HttpHeaders.CONTENT_TYPE, "text/json; charset=utf-8")
                .header("Encodeing", "utf8").body(mapper.writeValueAsString(body));
    }

    private String str(Map<String,Object> request, String key) {
        Object value = request.get(key);
        return value == null ? null : value.toString();
    }

    @SuppressWarnings("unchecked")
    private Map<String,Object> office(Map<String,Object> request, String key) {
        return (Map<String,Object>) request.get(key);
    }
}
