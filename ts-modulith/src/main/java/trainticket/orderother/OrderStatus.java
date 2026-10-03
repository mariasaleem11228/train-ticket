/* Deployed codewisdom OrderOther 0.2.0 DTO. */
package trainticket.orderother;

/*
 * Exception performing whole class analysis ignored.
 */
public enum OrderStatus {
    NOTPAID(0, "Not Paid"),
    PAID(1, "Paid & Not Collected"),
    COLLECTED(2, "Collected"),
    CHANGE(3, "Cancel & Rebook"),
    CANCEL(4, "Cancel"),
    REFUNDS(5, "Refunded"),
    USED(6, "Used");

    private int code;
    private String name;

    private OrderStatus(int code, String name) {
        this.code = code;
        this.name = name;
    }

    public int getCode() {
        return this.code;
    }

    public String getName() {
        return this.name;
    }

    public static String getNameByCode(int code) {
        OrderStatus[] orderStatusSet;
        for (OrderStatus orderStatus : orderStatusSet = OrderStatus.values()) {
            if (orderStatus.getCode() != code) continue;
            return orderStatus.getName();
        }
        return orderStatusSet[0].getName();
    }
}

