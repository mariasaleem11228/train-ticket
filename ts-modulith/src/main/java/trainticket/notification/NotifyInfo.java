package trainticket.notification;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.util.UUID;

/** Wire shape of the deployed Notification service. */
@JsonIgnoreProperties(ignoreUnknown=true)
public record NotifyInfo(UUID id, Boolean sendStatus, String email, String orderNumber,
                         String username, String startingPlace, String endPlace,
                         String startingTime, String date, String seatClass,
                         String seatNumber, String price) {
    public NotifyInfo delivered(UUID newId, boolean sent) {
        return new NotifyInfo(newId,sent,email,orderNumber,username,startingPlace,endPlace,
                startingTime,date,seatClass,seatNumber,price);
    }
}
