package trainticket.runtime;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import java.nio.file.Files;
import java.nio.file.Paths;

/** Per-module write gate for independent rollback while the shared host stays up. */
@Component
public class WriteOwnership {
    private final String path;
    private final ObjectMapper mapper = new ObjectMapper();
    public WriteOwnership(@Value("${modulith.ownership-file:}") String path) { this.path=path; }
    public boolean permits(String module) {
        if (path.isEmpty()) return true; // Isolated tests still require their explicit writes-enabled flag.
        try {
            JsonNode owners=mapper.readTree(Files.readAllBytes(Paths.get(path)));
            return "module".equals(owners.path(module).asText());
        } catch (Exception failure) {
            return false; // Missing/invalid ownership never grants write access.
        }
    }
}
