package trainticket.station.internal;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.modulith.test.ApplicationModuleTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import trainticket.station.Station;
import trainticket.station.StationOperations;
import java.util.List;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.when;

@ApplicationModuleTest
class StationModuleTest {
    @MockitoBean StationStore store;
    @Autowired StationOperations stations;

    @Test void exposesStationOperationsWithinItsModule() {
        when(store.findAll()).thenReturn(List.of(new Station("shanghai", "Shang Hai", 10)));
        assertEquals(1, stations.list().getStatus());
        assertEquals("Shang Hai", ((Station)((List<?>)stations.list().getData()).get(0)).getName());
    }
}
