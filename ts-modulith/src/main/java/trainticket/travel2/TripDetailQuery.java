package trainticket.travel2;

import java.util.Date;

public record TripDetailQuery(String tripId, Date travelDate, String from, String to) { }
