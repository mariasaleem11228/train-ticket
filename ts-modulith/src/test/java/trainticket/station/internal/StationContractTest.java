package trainticket.station.internal;

import org.junit.jupiter.api.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import trainticket.station.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

class StationContractTest {
    private MemoryStore store;
    private StationService service;
    private MockMvc mvc;
    @BeforeEach void setUp() {
        store = new MemoryStore();
        store.save(new Station("shanghai", "Shang Hai", 10));
        service = new StationService(store, true);
        mvc = MockMvcBuilders.standaloneSetup(new StationController(service)).build();
    }
    @Test void batchIdsPreserveOrderDuplicatesAndMissingSlots() throws Exception {
        mvc.perform(post("/api/v1/stationservice/stations/idlist").contentType("application/json")
                .content("[\"Shang Hai\",\"missing\",\"Shang Hai\"]"))
                .andExpect(status().isOk()).andExpect(content().json("{\"status\":1,\"msg\":\"Success\",\"data\":[\"shanghai\",\"Not Exist\",\"shanghai\"]}", true));
    }
    @Test void namesRetainCaseAndSpaces() {
        assertEquals("shanghai", service.idForName("Shang Hai").getData());
        assertEquals(0, service.idForName("shanghai").getStatus());
    }
    @Test void emptyAndUnknownBatchesHaveDifferentContracts() {
        assertNull(service.idsForNames(Collections.emptyList()).getData());
        assertEquals(Collections.emptyList(), service.namesForIds(Collections.singletonList("missing")).getData());
        assertEquals(Arrays.asList("Shang Hai", "Shang Hai"), service.namesForIds(Arrays.asList("shanghai", "missing", "shanghai")).getData());
    }
    @Test void createUsesSuppliedIdAndDuplicateIdSemantics() throws Exception {
        mvc.perform(post("/api/v1/stationservice/stations").contentType("application/json")
                .content("{\"id\":\"new\",\"name\":\"Shang Hai\",\"stayTime\":7}"))
                .andExpect(status().isCreated()).andExpect(jsonPath("$.status").value(1));
        assertEquals(0, service.create(new Station("new", "Other", 1)).getStatus());
        assertEquals("Shang Hai", store.findById("new").getName());
    }
    @Test void legacyDeleteUsesBodyAndReturnsSubmittedNameWithZeroStayTime() throws Exception {
        mvc.perform(delete("/api/v1/stationservice/stations").contentType("application/json")
                .content("{\"id\":\"shanghai\",\"name\":\"Submitted\",\"stayTime\":99}"))
                .andExpect(status().isOk()).andExpect(content().json("{\"status\":1,\"msg\":\"Delete success\",\"data\":{\"id\":\"shanghai\",\"name\":\"Submitted\",\"stayTime\":0}}", true));
        assertNull(store.findById("shanghai"));
    }
    @Test void candidateCannotWrite() {
        StationService candidate = new StationService(store, false);
        assertThrows(org.springframework.web.server.ResponseStatusException.class, () -> candidate.create(new Station()));
        assertThrows(org.springframework.web.server.ResponseStatusException.class, () -> candidate.update(new Station()));
        assertThrows(org.springframework.web.server.ResponseStatusException.class, () -> candidate.delete(new Station()));
        assertEquals(1, candidate.list().getStatus());
    }
    static class MemoryStore implements StationStore {
        final Map<String, Station> entries = new LinkedHashMap<>();
        public Station findById(String id) { return entries.get(id); }
        public Station findByName(String name) { return entries.values().stream().filter(s -> Objects.equals(s.getName(), name)).findFirst().orElse(null); }
        public List<Station> findAll() { return new ArrayList<>(entries.values()); }
        public void save(Station station) { entries.put(station.getId(), station); }
        public void delete(String id) { entries.remove(id); }
    }
}
