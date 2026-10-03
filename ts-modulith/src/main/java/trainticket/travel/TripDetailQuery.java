package trainticket.travel;

import java.util.Date;

public record TripDetailQuery(String tripId, Date travelDate, String from, String to) { }
