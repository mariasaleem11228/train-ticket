package trainticket.travelplan;

import java.util.Date;

public record TravelPlanQuery(String startingPlace, String endPlace, Date departureTime) { }
