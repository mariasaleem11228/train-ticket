/* Deployed codewisdom OrderOther 0.2.0 DTO. */
package trainticket.orderother;

import java.util.Date;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;

public class Seat {
    @Valid
    @NotNull
    private Date travelDate;
    @Valid
    @NotNull
    private String trainNumber;
    @Valid
    @NotNull
    private String startStation;
    @Valid
    @NotNull
    private String destStation;
    @Valid
    @NotNull
    private int seatType;

    public Seat() {
        this.travelDate = new Date();
        this.trainNumber = "";
        this.startStation = "";
        this.destStation = "";
        this.seatType = 0;
    }

    public Date getTravelDate() {
        return this.travelDate;
    }

    public String getTrainNumber() {
        return this.trainNumber;
    }

    public String getStartStation() {
        return this.startStation;
    }

    public String getDestStation() {
        return this.destStation;
    }

    public int getSeatType() {
        return this.seatType;
    }

    public void setTravelDate(Date travelDate) {
        this.travelDate = travelDate;
    }

    public void setTrainNumber(String trainNumber) {
        this.trainNumber = trainNumber;
    }

    public void setStartStation(String startStation) {
        this.startStation = startStation;
    }

    public void setDestStation(String destStation) {
        this.destStation = destStation;
    }

    public void setSeatType(int seatType) {
        this.seatType = seatType;
    }

    public boolean equals(Object o) {
        if (o == this) {
            return true;
        }
        if (!(o instanceof Seat)) {
            return false;
        }
        Seat other = (Seat)o;
        if (!other.canEqual((Object)this)) {
            return false;
        }
        Date this$travelDate = this.getTravelDate();
        Date other$travelDate = other.getTravelDate();
        if (this$travelDate == null ? other$travelDate != null : !((Object)this$travelDate).equals(other$travelDate)) {
            return false;
        }
        String this$trainNumber = this.getTrainNumber();
        String other$trainNumber = other.getTrainNumber();
        if (this$trainNumber == null ? other$trainNumber != null : !this$trainNumber.equals(other$trainNumber)) {
            return false;
        }
        String this$startStation = this.getStartStation();
        String other$startStation = other.getStartStation();
        if (this$startStation == null ? other$startStation != null : !this$startStation.equals(other$startStation)) {
            return false;
        }
        String this$destStation = this.getDestStation();
        String other$destStation = other.getDestStation();
        if (this$destStation == null ? other$destStation != null : !this$destStation.equals(other$destStation)) {
            return false;
        }
        return this.getSeatType() == other.getSeatType();
    }

    protected boolean canEqual(Object other) {
        return other instanceof Seat;
    }

    public int hashCode() {
        int PRIME = 59;
        int result = 1;
        Date $travelDate = this.getTravelDate();
        result = result * 59 + ($travelDate == null ? 43 : ((Object)$travelDate).hashCode());
        String $trainNumber = this.getTrainNumber();
        result = result * 59 + ($trainNumber == null ? 43 : $trainNumber.hashCode());
        String $startStation = this.getStartStation();
        result = result * 59 + ($startStation == null ? 43 : $startStation.hashCode());
        String $destStation = this.getDestStation();
        result = result * 59 + ($destStation == null ? 43 : $destStation.hashCode());
        result = result * 59 + this.getSeatType();
        return result;
    }

    public String toString() {
        return "Seat(travelDate=" + this.getTravelDate() + ", trainNumber=" + this.getTrainNumber() + ", startStation=" + this.getStartStation() + ", destStation=" + this.getDestStation() + ", seatType=" + this.getSeatType() + ")";
    }

    public Seat(Date travelDate, String trainNumber, String startStation, String destStation, int seatType) {
        this.travelDate = travelDate;
        this.trainNumber = trainNumber;
        this.startStation = startStation;
        this.destStation = destStation;
        this.seatType = seatType;
    }
}

