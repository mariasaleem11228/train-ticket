package trainticket;

import org.junit.jupiter.api.Test;
import org.springframework.modulith.core.ApplicationModules;
import java.util.stream.Collectors;
import java.util.stream.StreamSupport;
import static org.junit.jupiter.api.Assertions.assertEquals;

class SpringModulithStructureTest {
    @Test void verifiesBusinessModulesAndDependencies() {
        String previous=System.getProperty("spring.modulith.detection-strategy");
        System.setProperty("spring.modulith.detection-strategy", "explicitly-annotated");
        try {
            ApplicationModules modules = ApplicationModules.of(ModulithApplication.class);
            modules.verify();
            assertEquals(java.util.Set.of("station", "orders", "orderother", "config", "seat", "security", "train", "route", "price", "basic", "travel", "travel2", "routeplan", "travelplan", "contacts", "preserve", "preserveother", "execute", "payment", "insidepayment", "cancel", "rebook", "assurance", "consignprice", "consign", "foodmap", "food", "notification", "verifycode", "auth", "user", "adminbasic", "adminroute", "admintravel", "adminorder", "adminuser", "voucher", "news", "ticketoffice", "avatar", "delivery", "fooddelivery", "ticketinfo", "waitorder", "tripcatalog"),
                    StreamSupport.stream(modules.spliterator(), false)
                            .map(module -> module.getIdentifier().toString()).collect(Collectors.toSet()));
        } finally {
            if (previous==null)System.clearProperty("spring.modulith.detection-strategy");
            else System.setProperty("spring.modulith.detection-strategy",previous);
        }
    }
}
