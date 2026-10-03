/* Deployed codewisdom OrderOther 0.2.0 DTO. */
package trainticket.orderother;

public class OrderSecurity {
    private int orderNumInLastOneHour;
    private int orderNumOfValidOrder;

    public OrderSecurity() {
    }

    public int getOrderNumInLastOneHour() {
        return this.orderNumInLastOneHour;
    }

    public int getOrderNumOfValidOrder() {
        return this.orderNumOfValidOrder;
    }

    public void setOrderNumInLastOneHour(int orderNumInLastOneHour) {
        this.orderNumInLastOneHour = orderNumInLastOneHour;
    }

    public void setOrderNumOfValidOrder(int orderNumOfValidOrder) {
        this.orderNumOfValidOrder = orderNumOfValidOrder;
    }

    public boolean equals(Object o) {
        if (o == this) {
            return true;
        }
        if (!(o instanceof OrderSecurity)) {
            return false;
        }
        OrderSecurity other = (OrderSecurity)o;
        if (!other.canEqual((Object)this)) {
            return false;
        }
        if (this.getOrderNumInLastOneHour() != other.getOrderNumInLastOneHour()) {
            return false;
        }
        return this.getOrderNumOfValidOrder() == other.getOrderNumOfValidOrder();
    }

    protected boolean canEqual(Object other) {
        return other instanceof OrderSecurity;
    }

    public int hashCode() {
        int PRIME = 59;
        int result = 1;
        result = result * 59 + this.getOrderNumInLastOneHour();
        result = result * 59 + this.getOrderNumOfValidOrder();
        return result;
    }

    public String toString() {
        return "OrderSecurity(orderNumInLastOneHour=" + this.getOrderNumInLastOneHour() + ", orderNumOfValidOrder=" + this.getOrderNumOfValidOrder() + ")";
    }

    public OrderSecurity(int orderNumInLastOneHour, int orderNumOfValidOrder) {
        this.orderNumInLastOneHour = orderNumInLastOneHour;
        this.orderNumOfValidOrder = orderNumOfValidOrder;
    }
}

