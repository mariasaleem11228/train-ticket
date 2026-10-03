/* Ported from the deployed codewisdom/ts-order-service:0.2.0 classes.
 * Preserve benchmark behaviour; see docs/migration/orders-pilot-results.md. */
package trainticket.orders;

import java.util.Set;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;
import trainticket.orders.Ticket;

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
        if (!other.canEqual(this)) {
            return false;
        }
        Set<Ticket> this$soldTickets = this.getSoldTickets();
        Set<Ticket> other$soldTickets = other.getSoldTickets();
        return !(this$soldTickets == null ? other$soldTickets != null : !((Object)this$soldTickets).equals(other$soldTickets));
    }

    protected boolean canEqual(Object other) {
        return other instanceof LeftTicketInfo;
    }

    public int hashCode() {
        int PRIME = 59;
        int result = 1;
        Set<Ticket> $soldTickets = this.getSoldTickets();
        result = result * 59 + ($soldTickets == null ? 43 : ((Object)$soldTickets).hashCode());
        return result;
    }
}

