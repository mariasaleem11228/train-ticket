package trainticket.travel;

import java.util.Date;

public record TravelInfo(String tripId, String trainTypeId, String routeId,
                         String startingStationId, String stationsId, String terminalStationId,
                         Date startingTime, Date endTime) { }
