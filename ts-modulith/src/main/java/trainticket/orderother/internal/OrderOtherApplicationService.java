/* Ported from deployed codewisdom/ts-order-other-service:0.2.0. */
package trainticket.orderother.internal;

import trainticket.orderother.OrderOtherResult;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.HashSet;
import java.util.List;
import java.util.UUID;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import trainticket.orderother.LeftTicketInfo;
import trainticket.orderother.Order;
import trainticket.orderother.OrderAlterInfo;
import trainticket.orderother.OrderSecurity;
import trainticket.orderother.OrderStatus;
import trainticket.orderother.QueryInfo;
import trainticket.orderother.Seat;
import trainticket.orderother.SeatClass;
import trainticket.orderother.SoldTicket;
import trainticket.orderother.Ticket;

@Service
@org.springframework.boot.autoconfigure.condition.ConditionalOnProperty(name="modulith.order-other.enabled", havingValue="true")
public class OrderOtherApplicationService
implements trainticket.orderother.OrderOtherOperations {
    private final OrderOtherRepository orderOtherRepository;
    private final trainticket.station.StationOperations stations;
    public OrderOtherApplicationService(OrderOtherRepository orderOtherRepository,
                                        trainticket.station.StationOperations stations) {
        this.orderOtherRepository=orderOtherRepository;
        this.stations=stations;
    }
    private static final Logger LOGGER = LoggerFactory.getLogger(OrderOtherApplicationService.class);
    String success = "Success";
    String orderNotFound = "Order Not Found";

    public OrderOtherResult getSoldTickets(Seat seatRequest) {
        ArrayList<Order> list = this.orderOtherRepository.findByTravelDateAndTrainNumber(seatRequest.getTravelDate(), seatRequest.getTrainNumber());
        if (list != null && !list.isEmpty()) {
            HashSet<Ticket> ticketSet = new HashSet<Ticket>();
            for (Order tempOrder : list) {
                Ticket ticket = new Ticket();
                ticket.setSeatNo(Integer.parseInt(tempOrder.getSeatNumber()));
                ticket.setStartStation(tempOrder.getFrom());
                ticket.setDestStation(tempOrder.getTo());
                ticketSet.add(ticket);
            }
            LeftTicketInfo leftTicketInfo = new LeftTicketInfo();
            leftTicketInfo.setSoldTickets(ticketSet);
            LOGGER.info("Left ticket info is: {}", (Object)leftTicketInfo.toString());
            return new OrderOtherResult(Integer.valueOf(1), this.success, (Object)leftTicketInfo);
        }
        LOGGER.warn("No content, seat from date: {}, train number: {}", (Object)seatRequest.getTravelDate(), (Object)seatRequest.getTrainNumber());
        return new OrderOtherResult(Integer.valueOf(0), "Seat is Null.", null);
    }

    public OrderOtherResult findOrderById(UUID id) {
        Order order = this.orderOtherRepository.findById(id);
        if (order == null) {
            LOGGER.error("No content, id: {}", (Object)id);
            return new OrderOtherResult(Integer.valueOf(0), "No Content by this id", null);
        }
        return new OrderOtherResult(Integer.valueOf(1), this.success, (Object)order);
    }

    public OrderOtherResult create(Order order) {
        LOGGER.info("[Create Order] Ready Create Order");
        ArrayList accountOrders = this.orderOtherRepository.findByAccountId(order.getAccountId());
        if (accountOrders.contains(order)) {
            LOGGER.error("[Order Create] Fail.Order already exists, OrderId: {}", (Object)order.getId());
            return new OrderOtherResult(Integer.valueOf(0), "Order already exist", (Object)order);
        }
        order.setId(UUID.randomUUID());
        this.orderOtherRepository.save(order);
        LOGGER.info("[Order Create] Success.");
        LOGGER.info("[Order Create] Price: {}", (Object)order.getPrice());
        return new OrderOtherResult(Integer.valueOf(1), this.success, (Object)order);
    }

    public void initOrder(Order order) {
        Order orderTemp = this.orderOtherRepository.findById(order.getId());
        if (orderTemp == null) {
            this.orderOtherRepository.save(order);
        } else {
            LOGGER.error("[Init Order] Order Already Exists, OrderId: {}", (Object)order.getId());
        }
    }

    public OrderOtherResult alterOrder(OrderAlterInfo oai) {
        UUID oldOrderId = oai.getPreviousOrderId();
        Order oldOrder = this.orderOtherRepository.findById(oldOrderId);
        if (oldOrder == null) {
            LOGGER.error("[Alter Order] Fail.Order do not exist, OrderId: {}", (Object)oldOrderId);
            return new OrderOtherResult(Integer.valueOf(0), "Old Order Does Not Exists", null);
        }
        oldOrder.setStatus(OrderStatus.CANCEL.getCode());
        this.saveChanges(oldOrder);
        Order newOrder = oai.getNewOrderInfo();
        newOrder.setId(UUID.randomUUID());
        OrderOtherResult cor = this.create(oai.getNewOrderInfo());
        if (cor.getStatus() == 1) {
            LOGGER.info("[Alter Order] Success.");
            return new OrderOtherResult(Integer.valueOf(1), "Alter Order Success", (Object)newOrder);
        }
        LOGGER.error("Alter Order Fail.Create new order fail, OrderId: {}", (Object)newOrder.getId());
        return new OrderOtherResult(Integer.valueOf(0), cor.getMsg(), null);
    }

    public OrderOtherResult<ArrayList<Order>> queryOrders(QueryInfo qi, String accountId) {
        ArrayList<Order> list = this.orderOtherRepository.findByAccountId(UUID.fromString(accountId));
        LOGGER.info("[Query Order][Step 1] Get Orders Number of Account: {}", (Object)list.size());
        if (qi.isEnableStateQuery() || qi.isEnableBoughtDateQuery() || qi.isEnableTravelDateQuery()) {
            ArrayList<Order> finalList = new ArrayList<Order>();
            for (Order tempOrder : list) {
                boolean statePassFlag = false;
                boolean boughtDatePassFlag = false;
                boolean travelDatePassFlag = false;
                statePassFlag = qi.isEnableStateQuery() ? tempOrder.getStatus() == qi.getState() : true;
                LOGGER.info("[Query Order][Step 2][Check Status Fits End]");
                travelDatePassFlag = qi.isEnableTravelDateQuery() ? tempOrder.getTravelDate().before(qi.getTravelDateEnd()) && tempOrder.getTravelDate().after(qi.getBoughtDateStart()) : true;
                LOGGER.info("[Query Order][Step 2][Check Travel Date End]");
                boughtDatePassFlag = qi.isEnableBoughtDateQuery() ? tempOrder.getBoughtDate().before(qi.getBoughtDateEnd()) && tempOrder.getBoughtDate().after(qi.getBoughtDateStart()) : true;
                LOGGER.info("[Query Order][Step 2][Check Bought Date End]");
                if (statePassFlag && boughtDatePassFlag && travelDatePassFlag) {
                    finalList.add(tempOrder);
                }
                LOGGER.info("[Query Order][Step 2][Check All Requirement End]");
            }
            LOGGER.info("[Query Order] Get order num: {}", (Object)finalList.size());
            return new OrderOtherResult(Integer.valueOf(1), "Get order num", finalList);
        }
        LOGGER.warn("[Query Order] Orders don't fit the requirement, loginId: {}", (Object)qi.getLoginId());
        return new OrderOtherResult(Integer.valueOf(1), "Get order num", (Object)list);
    }

    public OrderOtherResult queryOrdersForRefresh(QueryInfo qi, String accountId) {
        ArrayList<Order> orders = (ArrayList<Order>)this.queryOrders(qi, accountId).getData();
        ArrayList<String> stationIds = new ArrayList<String>();
        for (Order order : orders) {
            stationIds.add(order.getFrom());
            stationIds.add(order.getTo());
        }
        List names = this.queryForStationId(stationIds);
        for (int i = 0; i < orders.size(); ++i) {
            ((Order)orders.get(i)).setFrom((String)names.get(i * 2));
            ((Order)orders.get(i)).setTo((String)names.get(i * 2 + 1));
        }
        return new OrderOtherResult(Integer.valueOf(1), this.success, (Object)orders);
    }

    public List<String> queryForStationId(List<String> ids) {
        return (List<String>) stations.namesForIds(ids).getData();
    }

    public OrderOtherResult saveChanges(Order order) {
        Order oldOrder = this.orderOtherRepository.findById(order.getId());
        if (oldOrder == null) {
            LOGGER.error("[Modify Order] Fail.Order not found, OrderId: {}", (Object)order.getId());
            return new OrderOtherResult(Integer.valueOf(0), this.orderNotFound, null);
        }
        oldOrder.setAccountId(order.getAccountId());
        oldOrder.setBoughtDate(order.getBoughtDate());
        oldOrder.setTravelDate(order.getTravelDate());
        oldOrder.setTravelTime(order.getTravelTime());
        oldOrder.setSeatClass(order.getSeatClass());
        oldOrder.setCoachNumber(order.getCoachNumber());
        oldOrder.setSeatNumber(order.getSeatNumber());
        oldOrder.setTo(order.getTo());
        oldOrder.setFrom(order.getFrom());
        oldOrder.setStatus(order.getStatus());
        oldOrder.setTrainNumber(order.getTrainNumber());
        oldOrder.setPrice(order.getPrice());
        oldOrder.setContactsName(order.getContactsName());
        oldOrder.setDocumentType(order.getDocumentType());
        oldOrder.setContactsDocumentNumber(order.getContactsDocumentNumber());
        this.orderOtherRepository.save(oldOrder);
        LOGGER.info(" Success.");
        return new OrderOtherResult(Integer.valueOf(1), this.success, (Object)oldOrder);
    }

    public OrderOtherResult cancelOrder(UUID accountId, UUID orderId) {
        Order oldOrder = this.orderOtherRepository.findById(orderId);
        if (oldOrder == null) {
            LOGGER.error("[Cancel Order] Fail.Order not found, OrderId: {}", (Object)orderId);
            return new OrderOtherResult(Integer.valueOf(0), this.orderNotFound, null);
        }
        oldOrder.setStatus(OrderStatus.CANCEL.getCode());
        this.orderOtherRepository.save(oldOrder);
        LOGGER.info("[Cancel Order] Success.");
        return new OrderOtherResult(Integer.valueOf(1), this.success, (Object)oldOrder);
    }

    public OrderOtherResult queryAlreadySoldOrders(Date travelDate, String trainNumber) {
        ArrayList<Order> orders = this.orderOtherRepository.findByTravelDateAndTrainNumber(travelDate, trainNumber);
        SoldTicket cstr = new SoldTicket();
        cstr.setTravelDate(travelDate);
        cstr.setTrainNumber(trainNumber);
        LOGGER.info("[Calculate Sold Ticket] Get Orders Number: {}", (Object)orders.size());
        for (Order order : orders) {
            if (order.getStatus() >= OrderStatus.CHANGE.getCode()) continue;
            if (order.getSeatClass() == SeatClass.NONE.getCode()) {
                cstr.setNoSeat(cstr.getNoSeat() + 1);
                continue;
            }
            if (order.getSeatClass() == SeatClass.BUSINESS.getCode()) {
                cstr.setBusinessSeat(cstr.getBusinessSeat() + 1);
                continue;
            }
            if (order.getSeatClass() == SeatClass.FIRSTCLASS.getCode()) {
                cstr.setFirstClassSeat(cstr.getFirstClassSeat() + 1);
                continue;
            }
            if (order.getSeatClass() == SeatClass.SECONDCLASS.getCode()) {
                cstr.setSecondClassSeat(cstr.getSecondClassSeat() + 1);
                continue;
            }
            if (order.getSeatClass() == SeatClass.HARDSEAT.getCode()) {
                cstr.setHardSeat(cstr.getHardSeat() + 1);
                continue;
            }
            if (order.getSeatClass() == SeatClass.SOFTSEAT.getCode()) {
                cstr.setSoftSeat(cstr.getSoftSeat() + 1);
                continue;
            }
            if (order.getSeatClass() == SeatClass.HARDBED.getCode()) {
                cstr.setHardBed(cstr.getHardBed() + 1);
                continue;
            }
            if (order.getSeatClass() == SeatClass.SOFTBED.getCode()) {
                cstr.setSoftBed(cstr.getSoftBed() + 1);
                continue;
            }
            if (order.getSeatClass() == SeatClass.HIGHSOFTBED.getCode()) {
                cstr.setHighSoftBed(cstr.getHighSoftBed() + 1);
                continue;
            }
            LOGGER.info("[Calculate Sold Tickets] Seat class not exists. Order ID: {}", (Object)order.getId());
        }
        return new OrderOtherResult(Integer.valueOf(1), this.success, (Object)cstr);
    }

    public OrderOtherResult getAllOrders() {
        ArrayList<Order> orders = this.orderOtherRepository.findAll();
        if (orders == null) {
            LOGGER.warn("Find all orders warn: {}", (Object)"No content");
            return new OrderOtherResult(Integer.valueOf(0), "No Content", null);
        }
        return new OrderOtherResult(Integer.valueOf(1), this.success, (Object)orders);
    }

    public OrderOtherResult modifyOrder(String orderId, int status) {
        Order order = this.orderOtherRepository.findById(UUID.fromString(orderId));
        if (order == null) {
            LOGGER.error("Modify order error.Order not found, OrderId: {}", (Object)orderId);
            return new OrderOtherResult(Integer.valueOf(0), this.orderNotFound, null);
        }
        order.setStatus(status);
        this.orderOtherRepository.save(order);
        return new OrderOtherResult(Integer.valueOf(1), this.success, (Object)order);
    }

    public OrderOtherResult getOrderPrice(String orderId) {
        Order order = this.orderOtherRepository.findById(UUID.fromString(orderId));
        if (order == null) {
            LOGGER.error("Get order price error.Order not found, OrderId: {}", (Object)orderId);
            return new OrderOtherResult(Integer.valueOf(0), this.orderNotFound, (Object)"-1.0");
        }
        LOGGER.info("[Order Other Service][Get Order Price] Price: {}", (Object)order.getPrice());
        return new OrderOtherResult(Integer.valueOf(1), this.success, (Object)order.getPrice());
    }

    public OrderOtherResult payOrder(String orderId) {
        Order order = this.orderOtherRepository.findById(UUID.fromString(orderId));
        if (order == null) {
            LOGGER.error("Pay order error.Order not found, OrderId: {}", (Object)orderId);
            return new OrderOtherResult(Integer.valueOf(0), this.orderNotFound, null);
        }
        order.setStatus(OrderStatus.PAID.getCode());
        this.orderOtherRepository.save(order);
        return new OrderOtherResult(Integer.valueOf(1), this.success, (Object)order);
    }

    public OrderOtherResult getOrderById(String orderId) {
        Order order = this.orderOtherRepository.findById(UUID.fromString(orderId));
        if (order == null) {
            LOGGER.error("Order not found, OrderId: {}", (Object)orderId);
            return new OrderOtherResult(Integer.valueOf(0), this.orderNotFound, null);
        }
        return new OrderOtherResult(Integer.valueOf(1), this.success, (Object)order);
    }

    public OrderOtherResult checkSecurityAboutOrder(Date dateFrom, String accountId) {
        OrderSecurity result = new OrderSecurity();
        ArrayList<Order> orders = this.orderOtherRepository.findByAccountId(UUID.fromString(accountId));
        int countOrderInOneHour = 0;
        int countTotalValidOrder = 0;
        Calendar ca = Calendar.getInstance();
        ca.setTime(dateFrom);
        ca.add(11, -1);
        dateFrom = ca.getTime();
        for (Order order : orders) {
            if (order.getStatus() == OrderStatus.NOTPAID.getCode() || order.getStatus() == OrderStatus.PAID.getCode() || order.getStatus() == OrderStatus.COLLECTED.getCode()) {
                ++countTotalValidOrder;
            }
            if (!order.getBoughtDate().after(dateFrom)) continue;
            ++countOrderInOneHour;
        }
        result.setOrderNumInLastOneHour(countOrderInOneHour);
        result.setOrderNumOfValidOrder(countTotalValidOrder);
        return new OrderOtherResult(Integer.valueOf(1), this.success, (Object)result);
    }

    public OrderOtherResult deleteOrder(String orderId) {
        UUID orderUuid = UUID.fromString(orderId);
        Order order = this.orderOtherRepository.findById(orderUuid);
        if (order == null) {
            LOGGER.error("Delete order error.Order not found, OrderId: {}", (Object)orderId);
            return new OrderOtherResult(Integer.valueOf(0), "Order Not Exist.", null);
        }
        this.orderOtherRepository.deleteById(orderUuid);
        return new OrderOtherResult(Integer.valueOf(1), this.success, (Object)orderUuid);
    }

    public OrderOtherResult addNewOrder(Order order) {
        LOGGER.info("[Admin Add Order] Ready Add Order.");
        ArrayList accountOrders = this.orderOtherRepository.findByAccountId(order.getAccountId());
        if (accountOrders.contains(order)) {
            LOGGER.error("[Admin Add Order] Fail.Order already exists, OrderId: {}", (Object)order.getId());
            return new OrderOtherResult(Integer.valueOf(0), "Order already exist", null);
        }
        order.setId(UUID.randomUUID());
        this.orderOtherRepository.save(order);
        LOGGER.info("[Admin Add Order] Success.");
        LOGGER.info("[Admin Add Order] Price: {}", (Object)order.getPrice());
        return new OrderOtherResult(Integer.valueOf(1), this.success, (Object)order);
    }

    public OrderOtherResult updateOrder(Order order) {
        LOGGER.info("UPDATE ORDER INFO :" + order.toString());
        Order oldOrder = this.orderOtherRepository.findById(order.getId());
        if (oldOrder == null) {
            LOGGER.error("[Admin Update Order] Fail.Order not found, OrderId: {}", (Object)order.getId());
            return new OrderOtherResult(Integer.valueOf(0), this.orderNotFound, null);
        }
        LOGGER.info("{}", (Object)oldOrder.toString());
        oldOrder.setAccountId(order.getAccountId());
        oldOrder.setBoughtDate(order.getBoughtDate());
        oldOrder.setTravelDate(order.getTravelDate());
        oldOrder.setTravelTime(order.getTravelTime());
        oldOrder.setCoachNumber(order.getCoachNumber());
        oldOrder.setSeatClass(order.getSeatClass());
        oldOrder.setSeatNumber(order.getSeatNumber());
        oldOrder.setFrom(order.getFrom());
        oldOrder.setTo(order.getTo());
        oldOrder.setStatus(order.getStatus());
        oldOrder.setTrainNumber(order.getTrainNumber());
        oldOrder.setPrice(order.getPrice());
        oldOrder.setContactsName(order.getContactsName());
        oldOrder.setContactsDocumentNumber(order.getContactsDocumentNumber());
        oldOrder.setDocumentType(order.getDocumentType());
        this.orderOtherRepository.save(oldOrder);
        LOGGER.info("[Admin Update Order] Success.");
        return new OrderOtherResult(Integer.valueOf(1), this.success, (Object)oldOrder);
    }
}

