package trainticket.waitorder.internal;

import java.util.Date;

record WaitOrderRecord(String id, Date travelTime, String accountId, String contactsId,
                       String contactsName, int contactsDocumentType, String contactsDocumentNumber,
                       String trainNumber, int seatType, String from, String to, String price,
                       Date waitUtilTime, Date createdTime, int status) { }
