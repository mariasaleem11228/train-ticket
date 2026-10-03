package trainticket.avatar;

import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.io.IOException;
import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

/** HTTP boundary for the colocated dlib image detector. */
@RestController
@ConditionalOnProperty(name = "modulith.avatar.enabled", havingValue = "true")
class AvatarController {
    private static final Duration TIMEOUT = Duration.ofSeconds(30);
    private final String worker;

    AvatarController(@Value("${modulith.avatar.worker}") String worker) {
        this.worker = worker;
    }

    @PostMapping(path = {"/api/v1/avatar", "/api/v1/avatar/"}, consumes = MediaType.APPLICATION_JSON_VALUE)
    ResponseEntity<String> avatar(@RequestBody JsonNode body) {
        JsonNode image = body.get("img");
        if (image == null || image.isNull() || image.asText().isEmpty()) {
            return ResponseEntity.badRequest().contentType(MediaType.APPLICATION_JSON)
                    .body("{\"msg\":\"need img in request body\"}");
        }
        Process process = null;
        try {
            process = new ProcessBuilder("python", "-u", worker)
                    .redirectError(ProcessBuilder.Redirect.INHERIT).start();
            try (var stdin = process.getOutputStream()) {
                stdin.write(image.asText().getBytes(StandardCharsets.US_ASCII));
            }
            var output = new ByteArrayOutputStream();
            var readError = new AtomicReference<IOException>();
            Process detector = process;
            Thread reader = Thread.ofVirtual().start(() -> {
                try {
                    detector.getInputStream().transferTo(output);
                } catch (IOException e) {
                    readError.set(e);
                }
            });
            if (!process.waitFor(TIMEOUT.toMillis(), TimeUnit.MILLISECONDS)) {
                process.destroyForcibly();
                return ResponseEntity.status(HttpStatus.GATEWAY_TIMEOUT).body("Avatar detector timed out");
            }
            reader.join(TimeUnit.SECONDS.toMillis(3));
            if (reader.isAlive() || readError.get() != null) {
                return ResponseEntity.internalServerError().body("Avatar detector output unavailable");
            }
            String result = output.toString(StandardCharsets.US_ASCII);
            if (process.exitValue() == 2) {
                return ResponseEntity.badRequest().contentType(MediaType.APPLICATION_JSON).body(result);
            }
            if (process.exitValue() != 0) {
                return ResponseEntity.internalServerError().contentType(MediaType.APPLICATION_JSON).body(result);
            }
            return ResponseEntity.ok().contentType(MediaType.parseMediaType("text/html; charset=utf-8"))
                    .body(result);
        } catch (IOException e) {
            return ResponseEntity.internalServerError().body("Avatar detector unavailable");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            if (process != null) process.destroyForcibly();
            return ResponseEntity.internalServerError().body("Avatar detector interrupted");
        }
    }
}
