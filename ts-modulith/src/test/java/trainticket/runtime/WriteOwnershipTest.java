package trainticket.runtime;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import java.nio.file.*;
import static org.junit.jupiter.api.Assertions.*;

class WriteOwnershipTest {
    @TempDir Path directory;
    @Test void missingMalformedAndUnlistedModulesCannotWrite() throws Exception {
        Path file=directory.resolve("ownership.json");
        WriteOwnership gate=new WriteOwnership(file.toString());
        assertFalse(gate.permits("orders"));
        Files.write(file,"invalid".getBytes());
        assertFalse(gate.permits("orders"));
        Files.write(file,"{\"station\":\"module\",\"orders\":\"legacy\"}".getBytes());
        assertTrue(gate.permits("station"));
        assertFalse(gate.permits("orders"));
        assertFalse(gate.permits("unknown"));
        Files.write(file,"{\"station\":\"module\",\"orders\":\"module\"}".getBytes());
        assertTrue(gate.permits("orders"));
    }
}
