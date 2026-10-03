package trainticket.preserve;

import java.util.Date;

/** Deployed Preserve request fields. The date accepts the legacy JSON date format. */
public record BookingRequest(String accountId, String contactsId, String tripId, int seatType,
                             Date date, String from, String to, int assurance, int foodType,
                             String stationName, String storeName, String foodName, double foodPrice,
                             String handleDate, String consigneeName, String consigneePhone,
                             double consigneeWeight, boolean isWithin) { }
