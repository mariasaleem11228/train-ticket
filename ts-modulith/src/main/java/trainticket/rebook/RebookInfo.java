package trainticket.rebook;

import java.util.Date;

/** Browser and deployed Rebook request shape. */
public class RebookInfo {
    private String loginId="";
    private String orderId="";
    private String oldTripId="";
    private String tripId="";
    private int seatType;
    private Date date=new Date();
    public String getLoginId(){return loginId;}
    public void setLoginId(String value){loginId=value;}
    public String getOrderId(){return orderId;}
    public void setOrderId(String value){orderId=value;}
    public String getOldTripId(){return oldTripId;}
    public void setOldTripId(String value){oldTripId=value;}
    public String getTripId(){return tripId;}
    public void setTripId(String value){tripId=value;}
    public int getSeatType(){return seatType;}
    public void setSeatType(int value){seatType=value;}
    public Date getDate(){return date;}
    public void setDate(Date value){date=value;}
}
