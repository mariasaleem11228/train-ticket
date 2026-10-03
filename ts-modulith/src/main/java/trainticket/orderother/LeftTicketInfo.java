/* Deployed codewisdom OrderOther 0.2.0 DTO. */
package trainticket.orderother;

import java.util.Set;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;
import trainticket.orderother.Ticket;

public class LeftTicketInfo {
    @Valid
    @NotNull
    private Set<Ticket> soldTickets;

    public String toString() {
        return "LeftTicketInfo{soldTickets=" + this.soldTickets + '}';
    }

    public Set<Ticket> getSoldTickets() {
        return this.soldTickets;
    }

    public void setSoldTickets(Set<Ticket> soldTickets) {
        this.soldTickets = soldTickets;
    }

    public boolean equals(Object o) {
        if (o == this) {
            return true;
        }
        if (!(o instanceof LeftTicketInfo)) {
            return false;
        }
        LeftTicketInfo other = (LeftTicketInfo)o;
        if (!other.canEqual((Object)this)) {
            return false;
        }
        Set this$soldTickets = this.getSoldTickets();
        Set other$soldTickets = other.getSoldTickets();
        return !(this$soldTickets == null ? other$soldTickets != null : !((Object)this$soldTickets).equals(other$soldTickets));
    }

    protected boolean canEqual(Object other) {
        return other instanceof LeftTicketInfo;
    }

    public int hashCode() {
        int PRIME = 59;
        int result = 1;
        Set $soldTickets = this.getSoldTickets();
        result = result * 59 + ($soldTickets == null ? 43 : ((Object)$soldTickets).hashCode());
        return result;
    }
}

