package trainticket.travel;

public record TripId(String type, String number) {
    public static TripId parse(String value) {
        if (value == null || value.length() < 2) throw new IllegalArgumentException("Invalid trip ID");
        return new TripId(value.substring(0, 1), value.substring(1));
    }
    @Override public String toString() { return type + number; }
}
