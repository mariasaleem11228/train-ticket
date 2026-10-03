/* Deployed codewisdom OrderOther 0.2.0 DTO. */
package trainticket.orderother;

public class Ticket {
    private int seatNo;
    private String startStation;
    private String destStation;

    public int getSeatNo() {
        return this.seatNo;
    }

    public String getStartStation() {
        return this.startStation;
    }

    public String getDestStation() {
        return this.destStation;
    }

    public void setSeatNo(int seatNo) {
        this.seatNo = seatNo;
    }

    public void setStartStation(String startStation) {
        this.startStation = startStation;
    }

    public void setDestStation(String destStation) {
        this.destStation = destStation;
    }

    public boolean equals(Object o) {
        if (o == this) {
            return true;
        }
        if (!(o instanceof Ticket)) {
            return false;
        }
        Ticket other = (Ticket)o;
        if (!other.canEqual((Object)this)) {
            return false;
        }
        if (this.getSeatNo() != other.getSeatNo()) {
            return false;
        }
        String this$startStation = this.getStartStation();
        String other$startStation = other.getStartStation();
        if (this$startStation == null ? other$startStation != null : !this$startStation.equals(other$startStation)) {
            return false;
        }
        String this$destStation = this.getDestStation();
        String other$destStation = other.getDestStation();
        return !(this$destStation == null ? other$destStation != null : !this$destStation.equals(other$destStation));
    }

    protected boolean canEqual(Object other) {
        return other instanceof Ticket;
    }

    public int hashCode() {
        int PRIME = 59;
        int result = 1;
        result = result * 59 + this.getSeatNo();
        String $startStation = this.getStartStation();
        result = result * 59 + ($startStation == null ? 43 : $startStation.hashCode());
        String $destStation = this.getDestStation();
        result = result * 59 + ($destStation == null ? 43 : $destStation.hashCode());
        return result;
    }

    public String toString() {
        return "Ticket(seatNo=" + this.getSeatNo() + ", startStation=" + this.getStartStation() + ", destStation=" + this.getDestStation() + ")";
    }
}

