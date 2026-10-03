package trainticket.seat;

public interface SeatOperations {
    SeatResult<SeatTicket> distribute(SeatRequest request);
    SeatResult<Integer> leftTickets(SeatRequest request);
}
