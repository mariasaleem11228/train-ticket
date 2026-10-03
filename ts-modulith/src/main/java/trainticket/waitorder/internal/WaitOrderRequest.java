package trainticket.waitorder.internal;

record WaitOrderRequest(String accountId, String contactsId, String tripId, int seatType,
                        String date, String from, String to, String price) { }
