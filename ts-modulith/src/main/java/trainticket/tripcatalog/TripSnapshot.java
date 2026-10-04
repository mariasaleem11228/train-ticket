package trainticket.tripcatalog;

import java.util.Date;

/** Immutable view of a trip record, independent of either travel API. */
public record TripSnapshot(String tripId, String trainTypeId, String routeId, Date startingTime,
                           String startingStationId, String stationsId,
                           String terminalStationId, Date endTime) { }
