package trainticket.preserve;

public interface PreserveOperations {
    BookingResult book(BookingRequest request, String authorization);
}
