package trainticket.travel;

import java.util.Date;

/** Deployed Travel JSON and Mongo record fields. */
public record Trip(TripId tripId, String trainTypeId, String routeId, Date startingTime,
                   String startingStationId, String stationsId, String terminalStationId, Date endTime) { }
