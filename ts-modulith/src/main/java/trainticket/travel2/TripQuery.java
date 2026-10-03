package trainticket.travel2;

import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.databind.annotation.JsonDeserialize;
import java.util.Date;
import trainticket.runtime.LegacyDepartureDateDeserializer;

public record TripQuery(@JsonAlias("startPlace") String startingPlace, String endPlace,
                        @JsonDeserialize(using = LegacyDepartureDateDeserializer.class) Date departureTime) { }
