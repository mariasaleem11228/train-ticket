/* Deployed codewisdom OrderOther 0.2.0 DTO. */
package trainticket.orderother;

/*
 * Exception performing whole class analysis ignored.
 */
public enum TrainType {
    GAOTIE(0, "G"),
    DONGCHE(1, "D"),
    CHENGJI(2, "C"),
    ZHIDA(3, "Z"),
    TEKUAI(4, "T"),
    KUAISU(5, "K"),
    LINKE(6, "L"),
    YOULAN(7, "Y"),
    CHENGJIAO(8, "S"),
    OTHER(9, "");

    private int code;
    private String name;

    private TrainType(int code, String name) {
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
        TrainType[] trainTypeSet;
        for (TrainType trainType : trainTypeSet = TrainType.values()) {
            if (trainType.getCode() != code) continue;
            return trainType.getName();
        }
        return trainTypeSet[0].getName();
    }
}

