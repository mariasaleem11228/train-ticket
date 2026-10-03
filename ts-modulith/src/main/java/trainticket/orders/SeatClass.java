/* Ported from the deployed codewisdom/ts-order-service:0.2.0 classes.
 * Preserve benchmark behaviour; see docs/migration/orders-pilot-results.md. */
package trainticket.orders;

public enum SeatClass {
    NONE(0, "NoSeat"),
    BUSINESS(1, "GreenSeat"),
    FIRSTCLASS(2, "FirstClassSeat"),
    SECONDCLASS(3, "SecondClassSeat"),
    HARDSEAT(4, "HardSeat"),
    SOFTSEAT(5, "SoftSeat"),
    HARDBED(6, "HardBed"),
    SOFTBED(7, "SoftBed"),
    HIGHSOFTBED(8, "HighSoftSeat");

    private int code;
    private String name;

    private SeatClass(int code, String name) {
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
        SeatClass[] seatClassSet;
        for (SeatClass seatClass : seatClassSet = SeatClass.values()) {
            if (seatClass.getCode() != code) continue;
            return seatClass.getName();
        }
        return seatClassSet[0].getName();
    }
}

