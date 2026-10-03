package trainticket.news;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

/** The deployed Go service serves this fixed body for every GET path. */
@RestController
@ConditionalOnProperty(name = "modulith.news.enabled", havingValue = "true")
class NewsController {
    static final String BODY = "[\n"
            + "                       {\"Title\": \"News Service Complete\", \"Content\": \"Congratulations:Your News Service Complete\"},\n"
            + "                       {\"Title\": \"Total Ticket System Complete\", \"Content\": \"Just a total test\"}\n"
            + "                    ]";

    @GetMapping({"/news-service", "/news-service/**"})
    ResponseEntity<String> news() {
        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_TYPE, "text/html; charset=utf-8")
                .body(BODY);
    }
}
