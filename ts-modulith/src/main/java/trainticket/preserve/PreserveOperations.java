package trainticket.preserve;

public interface PreserveOperations {
    BookingResult book(BookingRequest request, String authorization);
    /** Internal wait-list retry with a stable order ID and no optional purchases. */
    BookingResult bookWaitOrder(BookingRequest request, java.util.UUID orderId);
}
