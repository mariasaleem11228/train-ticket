/* Deployed codewisdom OrderOther 0.2.0 DTO. */
package trainticket.orderother;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.util.Date;
import java.util.UUID;
import trainticket.orderother.OrderStatus;
import trainticket.orderother.SeatClass;

@JsonIgnoreProperties(ignoreUnknown=true)
public class Order {
        private UUID id;
    private Date boughtDate = new Date(System.currentTimeMillis());
    private Date travelDate = new Date(123456789L);
    private Date travelTime;
    private UUID accountId;
    private String contactsName;
    private int documentType;
    private String contactsDocumentNumber;
    private String trainNumber = "G1235";
    private int coachNumber = 5;
    private int seatClass = SeatClass.FIRSTCLASS.getCode();
    private String seatNumber = "1";
    private String from = "shanghai";
    private String to = "taiyuan";
    private int status = OrderStatus.PAID.getCode();
    private String price = "0.0";

    public boolean equals(Object obj) {
        if (this == obj) {
            return true;
        }
        if (obj == null) {
            return false;
        }
        if (this.getClass() != obj.getClass()) {
            return false;
        }
        Order other = (Order)obj;
        return this.boughtDate.equals(other.getBoughtDate()) && this.travelDate.equals(other.getTravelDate()) && this.travelTime.equals(other.getTravelTime()) && this.accountId.equals(other.getAccountId()) && this.contactsName.equals(other.getContactsName()) && this.contactsDocumentNumber.equals(other.getContactsDocumentNumber()) && this.documentType == other.getDocumentType() && this.trainNumber.equals(other.getTrainNumber()) && this.coachNumber == other.getCoachNumber() && this.seatClass == other.getSeatClass() && this.seatNumber.equals(other.getSeatNumber()) && this.from.equals(other.getFrom()) && this.to.equals(other.getTo()) && this.status == other.getStatus() && this.price.equals(other.price);
    }

    public int hashCode() {
        int result = 17;
        result = 31 * result + (this.id == null ? 0 : this.id.hashCode());
        return result;
    }

    public void setTravelDate(int year, int month, int day) {
        Date date;
        this.travelDate = date = new Date(year, month, day, 0, 0, 0);
    }

    public UUID getId() {
        return this.id;
    }

    public Date getBoughtDate() {
        return this.boughtDate;
    }

    public Date getTravelDate() {
        return this.travelDate;
    }

    public Date getTravelTime() {
        return this.travelTime;
    }

    public UUID getAccountId() {
        return this.accountId;
    }

    public String getContactsName() {
        return this.contactsName;
    }

    public int getDocumentType() {
        return this.documentType;
    }

    public String getContactsDocumentNumber() {
        return this.contactsDocumentNumber;
    }

    public String getTrainNumber() {
        return this.trainNumber;
    }

    public int getCoachNumber() {
        return this.coachNumber;
    }

    public int getSeatClass() {
        return this.seatClass;
    }

    public String getSeatNumber() {
        return this.seatNumber;
    }

    public String getFrom() {
        return this.from;
    }

    public String getTo() {
        return this.to;
    }

    public int getStatus() {
        return this.status;
    }

    public String getPrice() {
        return this.price;
    }

    public void setId(UUID id) {
        this.id = id;
    }

    public void setBoughtDate(Date boughtDate) {
        this.boughtDate = boughtDate;
    }

    public void setTravelDate(Date travelDate) {
        this.travelDate = travelDate;
    }

    public void setTravelTime(Date travelTime) {
        this.travelTime = travelTime;
    }

    public void setAccountId(UUID accountId) {
        this.accountId = accountId;
    }

    public void setContactsName(String contactsName) {
        this.contactsName = contactsName;
    }

    public void setDocumentType(int documentType) {
        this.documentType = documentType;
    }

    public void setContactsDocumentNumber(String contactsDocumentNumber) {
        this.contactsDocumentNumber = contactsDocumentNumber;
    }

    public void setTrainNumber(String trainNumber) {
        this.trainNumber = trainNumber;
    }

    public void setCoachNumber(int coachNumber) {
        this.coachNumber = coachNumber;
    }

    public void setSeatClass(int seatClass) {
        this.seatClass = seatClass;
    }

    public void setSeatNumber(String seatNumber) {
        this.seatNumber = seatNumber;
    }

    public void setFrom(String from) {
        this.from = from;
    }

    public void setTo(String to) {
        this.to = to;
    }

    public void setStatus(int status) {
        this.status = status;
    }

    public void setPrice(String price) {
        this.price = price;
    }

    public String toString() {
        return "Order(id=" + this.getId() + ", boughtDate=" + this.getBoughtDate() + ", travelDate=" + this.getTravelDate() + ", travelTime=" + this.getTravelTime() + ", accountId=" + this.getAccountId() + ", contactsName=" + this.getContactsName() + ", documentType=" + this.getDocumentType() + ", contactsDocumentNumber=" + this.getContactsDocumentNumber() + ", trainNumber=" + this.getTrainNumber() + ", coachNumber=" + this.getCoachNumber() + ", seatClass=" + this.getSeatClass() + ", seatNumber=" + this.getSeatNumber() + ", from=" + this.getFrom() + ", to=" + this.getTo() + ", status=" + this.getStatus() + ", price=" + this.getPrice() + ")";
    }
}

