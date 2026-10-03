package trainticket.seat.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import trainticket.config.ConfigOperations;
import trainticket.orderother.OrderOtherOperations;
import trainticket.orders.OrderOperations;
import trainticket.seat.SeatOperations;
import trainticket.seat.SeatRequest;
import trainticket.seat.SeatResult;
import trainticket.seat.SeatTicket;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/** Seat rules ported from the deployed 0.2.0 JAR; Order and Config calls are local. */
@Service
@ConditionalOnProperty(name="modulith.seat.enabled", havingValue="true")
class SeatApplicationService implements SeatOperations {
    private final OrderOperations orders;
    private final OrderOtherOperations orderOther;
    private final ConfigOperations config;
    private final TravelLookup travel;
    private final Random random = new Random();

    SeatApplicationService(OrderOperations orders, OrderOtherOperations orderOther,
                           ConfigOperations config, TravelLookup travel) {
        this.orders = orders;
        this.orderOther = orderOther;
        this.config = config;
        this.travel = travel;
    }
    public SeatResult<SeatTicket> distribute(SeatRequest request) {
        boolean standard = standard(request);
        List<String> stations = travel.stations(request.getTrainNumber(), standard);
        List<SeatTicket> sold = sold(request, standard);
        int capacity = travel.capacity(request.getTrainNumber(), standard, request.getSeatType());
        int seat = random.nextInt(capacity) + 1;
        for (SeatTicket ticket : sold) {
            if (stations.indexOf(ticket.destStation()) < stations.indexOf(request.getStartStation()))
                return new SeatResult<>(1, "Use the previous distributed seat number!",
                        new SeatTicket(ticket.seatNo(), request.getStartStation(), request.getDestStation()));
        }
        // The deployed service can loop forever when every seat is sold. Fail promptly instead.
        if (sold.stream().map(SeatTicket::seatNo).distinct().count() >= capacity)
            return new SeatResult<>(0, "No seat available", null);
        while (contains(sold, seat)) seat = random.nextInt(capacity) + 1;
        return new SeatResult<>(1, "Use a new seat number!",
                new SeatTicket(seat, request.getStartStation(), request.getDestStation()));
    }
    public SeatResult<Integer> leftTickets(SeatRequest request) {
        boolean standard = standard(request);
        List<String> stations = travel.stations(request.getTrainNumber(), standard);
        List<SeatTicket> sold = sold(request, standard);
        int capacity = travel.capacity(request.getTrainNumber(), standard, request.getSeatType());
        int reusable = 0;
        for (SeatTicket ticket : sold)
            if (stations.indexOf(ticket.destStation()) < stations.indexOf(request.getStartStation())) reusable++;
        double proportion = Double.parseDouble(config.find("DirectTicketAllocationProportion").data().getValue());
        if (!stations.get(0).equals(request.getStartStation()) ||
                !stations.get(stations.size() - 1).equals(request.getDestStation()))
            proportion = 1.0 - proportion;
        return new SeatResult<>(1, "Get Left Ticket of Internal Success",
                reusable + (int)(capacity * proportion) - sold.size());
    }
    private boolean standard(SeatRequest request) {
        return request.getTrainNumber().startsWith("G") || request.getTrainNumber().startsWith("D");
    }
    private List<SeatTicket> sold(SeatRequest request, boolean standard) {
        List<SeatTicket> tickets = new ArrayList<>();
        if (standard) {
            trainticket.orders.Seat orderRequest = new trainticket.orders.Seat();
            orderRequest.setTravelDate(request.getTravelDate());
            orderRequest.setTrainNumber(request.getTrainNumber());
            orderRequest.setStartStation(request.getStartStation());
            orderRequest.setDestStation(request.getDestStation());
            orderRequest.setSeatType(request.getSeatType());
            Object data = orders.getSoldTickets(orderRequest).getData();
            if (data != null) for (trainticket.orders.Ticket ticket : ((trainticket.orders.LeftTicketInfo)data).getSoldTickets())
                tickets.add(new SeatTicket(ticket.getSeatNo(), ticket.getStartStation(), ticket.getDestStation()));
        } else {
            trainticket.orderother.Seat orderRequest = new trainticket.orderother.Seat();
            orderRequest.setTravelDate(request.getTravelDate());
            orderRequest.setTrainNumber(request.getTrainNumber());
            orderRequest.setStartStation(request.getStartStation());
            orderRequest.setDestStation(request.getDestStation());
            orderRequest.setSeatType(request.getSeatType());
            Object data = orderOther.getSoldTickets(orderRequest).getData();
            if (data != null) for (trainticket.orderother.Ticket ticket : ((trainticket.orderother.LeftTicketInfo)data).getSoldTickets())
                tickets.add(new SeatTicket(ticket.getSeatNo(), ticket.getStartStation(), ticket.getDestStation()));
        }
        return tickets;
    }
    private boolean contains(List<SeatTicket> tickets, int number) {
        for (SeatTicket ticket : tickets) if (ticket.seatNo() == number) return true;
        return false;
    }
}
