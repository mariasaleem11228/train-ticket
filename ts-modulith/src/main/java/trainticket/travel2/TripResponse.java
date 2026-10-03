package trainticket.travel2;

import java.util.Date;

public record TripResponse(TripId tripId, String trainTypeId, String startingStation,
                           String terminalStation, Date startingTime, Date endTime,
                           int economyClass, int confortClass, String priceForEconomyClass,
                           String priceForConfortClass) { }
