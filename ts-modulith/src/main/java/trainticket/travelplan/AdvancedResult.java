package trainticket.travelplan;

import java.util.Date;
import java.util.List;

public record AdvancedResult(String tripId, String trainTypeId, String fromStationName,
        String toStationName, List<String> stopStations,
        String priceForSecondClassSeat, int numberOfRestTicketSecondClass,
        String priceForFirstClassSeat, int numberOfRestTicketFirstClass,
        Date startingTime, Date endTime) { }
