/* Ported from the deployed codewisdom/ts-order-service:0.2.0 classes.
 * Preserve benchmark behaviour; see docs/migration/orders-pilot-results.md. */
package trainticket.orders;

import java.util.Date;

public class SoldTicket {
    private Date travelDate;
    private String trainNumber;
    private int noSeat = 0;
    private int businessSeat = 0;
    private int firstClassSeat = 0;
    private int secondClassSeat = 0;
    private int hardSeat = 0;
    private int softSeat = 0;
    private int hardBed = 0;
    private int softBed = 0;
    private int highSoftBed = 0;

    public Date getTravelDate() {
        return this.travelDate;
    }

    public String getTrainNumber() {
        return this.trainNumber;
    }

    public int getNoSeat() {
        return this.noSeat;
    }

    public int getBusinessSeat() {
        return this.businessSeat;
    }

    public int getFirstClassSeat() {
        return this.firstClassSeat;
    }

    public int getSecondClassSeat() {
        return this.secondClassSeat;
    }

    public int getHardSeat() {
        return this.hardSeat;
    }

    public int getSoftSeat() {
        return this.softSeat;
    }

    public int getHardBed() {
        return this.hardBed;
    }

    public int getSoftBed() {
        return this.softBed;
    }

    public int getHighSoftBed() {
        return this.highSoftBed;
    }

    public void setTravelDate(Date travelDate) {
        this.travelDate = travelDate;
    }

    public void setTrainNumber(String trainNumber) {
        this.trainNumber = trainNumber;
    }

    public void setNoSeat(int noSeat) {
        this.noSeat = noSeat;
    }

    public void setBusinessSeat(int businessSeat) {
        this.businessSeat = businessSeat;
    }

    public void setFirstClassSeat(int firstClassSeat) {
        this.firstClassSeat = firstClassSeat;
    }

    public void setSecondClassSeat(int secondClassSeat) {
        this.secondClassSeat = secondClassSeat;
    }

    public void setHardSeat(int hardSeat) {
        this.hardSeat = hardSeat;
    }

    public void setSoftSeat(int softSeat) {
        this.softSeat = softSeat;
    }

    public void setHardBed(int hardBed) {
        this.hardBed = hardBed;
    }

    public void setSoftBed(int softBed) {
        this.softBed = softBed;
    }

    public void setHighSoftBed(int highSoftBed) {
        this.highSoftBed = highSoftBed;
    }

    public boolean equals(Object o) {
        if (o == this) {
            return true;
        }
        if (!(o instanceof SoldTicket)) {
            return false;
        }
        SoldTicket other = (SoldTicket)o;
        if (!other.canEqual(this)) {
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
        if (this.getNoSeat() != other.getNoSeat()) {
            return false;
        }
        if (this.getBusinessSeat() != other.getBusinessSeat()) {
            return false;
        }
        if (this.getFirstClassSeat() != other.getFirstClassSeat()) {
            return false;
        }
        if (this.getSecondClassSeat() != other.getSecondClassSeat()) {
            return false;
        }
        if (this.getHardSeat() != other.getHardSeat()) {
            return false;
        }
        if (this.getSoftSeat() != other.getSoftSeat()) {
            return false;
        }
        if (this.getHardBed() != other.getHardBed()) {
            return false;
        }
        if (this.getSoftBed() != other.getSoftBed()) {
            return false;
        }
        return this.getHighSoftBed() == other.getHighSoftBed();
    }

    protected boolean canEqual(Object other) {
        return other instanceof SoldTicket;
    }

    public int hashCode() {
        int PRIME = 59;
        int result = 1;
        Date $travelDate = this.getTravelDate();
        result = result * 59 + ($travelDate == null ? 43 : ((Object)$travelDate).hashCode());
        String $trainNumber = this.getTrainNumber();
        result = result * 59 + ($trainNumber == null ? 43 : $trainNumber.hashCode());
        result = result * 59 + this.getNoSeat();
        result = result * 59 + this.getBusinessSeat();
        result = result * 59 + this.getFirstClassSeat();
        result = result * 59 + this.getSecondClassSeat();
        result = result * 59 + this.getHardSeat();
        result = result * 59 + this.getSoftSeat();
        result = result * 59 + this.getHardBed();
        result = result * 59 + this.getSoftBed();
        result = result * 59 + this.getHighSoftBed();
        return result;
    }

    public String toString() {
        return "SoldTicket(travelDate=" + this.getTravelDate() + ", trainNumber=" + this.getTrainNumber() + ", noSeat=" + this.getNoSeat() + ", businessSeat=" + this.getBusinessSeat() + ", firstClassSeat=" + this.getFirstClassSeat() + ", secondClassSeat=" + this.getSecondClassSeat() + ", hardSeat=" + this.getHardSeat() + ", softSeat=" + this.getSoftSeat() + ", hardBed=" + this.getHardBed() + ", softBed=" + this.getSoftBed() + ", highSoftBed=" + this.getHighSoftBed() + ")";
    }
}

