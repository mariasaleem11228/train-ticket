package trainticket;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

class TripQueryBrowserFormatTest {
    private final ObjectMapper mapper = new ObjectMapper();

    @Test void bothTravelModulesAcceptTheExistingBrowserSearchBody() throws Exception {
        String browser = """
                {"startPlace":"Nan Jing","endPlace":"Shang Hai","departureTime":"2026-10-08 00:00:00"}
                """;
        String api = """
                {"startingPlace":"Nan Jing","endPlace":"Shang Hai","departureTime":"2026-10-08"}
                """;
        for (Class<?> type : new Class<?>[] {trainticket.travel.TripQuery.class,
                trainticket.travel2.TripQuery.class}) {
            Object ui = mapper.readValue(browser, type);
            Object direct = mapper.readValue(api, type);
            assertEquals(direct, ui);
        }
    }
}
