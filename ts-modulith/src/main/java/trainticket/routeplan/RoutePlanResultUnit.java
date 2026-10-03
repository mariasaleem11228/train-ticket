package trainticket.routeplan;

import java.util.Date;
import java.util.List;

public record RoutePlanResultUnit(String tripId, String trainTypeId,
        String fromStationName, String toStationName, List<String> stopStations,
        String priceForSecondClassSeat, String priceForFirstClassSeat,
        Date startingTime, Date endTime) { }
