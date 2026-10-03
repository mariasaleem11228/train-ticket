/* Ported from the deployed codewisdom/ts-order-service:0.2.0 classes.
 * Preserve benchmark behaviour; see docs/migration/orders-pilot-results.md. */
package trainticket.orders.internal;

import trainticket.orders.OrderResult;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.HashSet;
import java.util.List;
import java.util.UUID;
import trainticket.orders.LeftTicketInfo;
import trainticket.orders.Order;
import trainticket.orders.OrderAlterInfo;
import trainticket.orders.OrderInfo;
import trainticket.orders.OrderSecurity;
import trainticket.orders.OrderStatus;
import trainticket.orders.Seat;
import trainticket.orders.SeatClass;
import trainticket.orders.SoldTicket;
import trainticket.orders.Ticket;

import trainticket.orders.OrderOperations;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import trainticket.station.StationOperations;

@Service
@org.springframework.boot.autoconfigure.condition.ConditionalOnProperty(name="modulith.orders.enabled", havingValue="true")
public class OrderApplicationService
implements OrderOperations {
    private final OrderRepository orderRepository;
    private final StationOperations stations;
    public OrderApplicationService(OrderRepository orderRepository, StationOperations stations) {
        this.orderRepository=orderRepository;
        this.stations=stations;
    }
    private static final Logger LOGGER = LoggerFactory.getLogger(OrderApplicationService.class);
    String success = "Success";
    String orderNotFound = "Order Not Found";

    @Override
    public OrderResult getSoldTickets(Seat seatRequest) {
        ArrayList<Order> list = this.orderRepository.findByTravelDateAndTrainNumber(seatRequest.getTravelDate(), seatRequest.getTrainNumber());
        if (list != null && !list.isEmpty()) {
            HashSet<Ticket> ticketSet = new HashSet<Ticket>();
            for (Order tempOrder : list) {
                ticketSet.add(new Ticket(Integer.parseInt(tempOrder.getSeatNumber()), tempOrder.getFrom(), tempOrder.getTo()));
            }
            LeftTicketInfo leftTicketInfo = new LeftTicketInfo();
            leftTicketInfo.setSoldTickets(ticketSet);
            LOGGER.info("Left ticket info is: {}", (Object)leftTicketInfo.toString());
            return new OrderResult(Integer.valueOf(1), this.success, (Object)leftTicketInfo);
        }
        LOGGER.error("Left ticket info is empty, seat from date: {}, train number: {}", (Object)seatRequest.getTravelDate(), (Object)seatRequest.getTrainNumber());
        return new OrderResult(Integer.valueOf(0), "Order is Null.", null);
    }

    @Override
    public OrderResult findOrderById(UUID id) {
        Order order = this.orderRepository.findById(id);
        if (order == null) {
            LOGGER.error("No content, id: {}", (Object)id);
            return new OrderResult(Integer.valueOf(0), "No Content by this id", null);
        }
        return new OrderResult(Integer.valueOf(1), this.success, (Object)order);
    }

    @Override
    public OrderResult create(Order order) {
        LOGGER.info("[Create Order] Ready Create Order.");
        ArrayList<Order> accountOrders = this.orderRepository.findByAccountId(order.getAccountId());
        if (accountOrders.contains(order)) {
            LOGGER.error("[Order Create] Fail.Order already exists, OrderId: {}", (Object)order.getId());
            return new OrderResult(Integer.valueOf(0), "Order already exist", null);
        }
        order.setId(UUID.randomUUID());
        this.orderRepository.save(order);
        LOGGER.info("[Order Create] Success.");
        LOGGER.info("[Order Create] Price: {}", (Object)order.getPrice());
        return new OrderResult(Integer.valueOf(1), this.success, (Object)order);
    }

    @Override
    public OrderResult alterOrder(OrderAlterInfo oai) {
        UUID oldOrderId = oai.getPreviousOrderId();
        Order oldOrder = this.orderRepository.findById(oldOrderId);
        if (oldOrder == null) {
            LOGGER.error("[Alter Order] Fail.Order do not exist, OrderId: {}", (Object)oldOrderId);
            return new OrderResult(Integer.valueOf(0), "Old Order Does Not Exists", null);
        }
        oldOrder.setStatus(OrderStatus.CANCEL.getCode());
        this.saveChanges(oldOrder);
        Order newOrder = oai.getNewOrderInfo();
        newOrder.setId(UUID.randomUUID());
        OrderResult cor = this.create(oai.getNewOrderInfo());
        if (cor.getStatus() == 1) {
            LOGGER.info("[Alter Order] Success.");
            return new OrderResult(Integer.valueOf(1), this.success, (Object)newOrder);
        }
        LOGGER.error("Alter Order Fail.Create new order fail, OrderId: {}", (Object)newOrder.getId());
        return new OrderResult(Integer.valueOf(0), cor.getMsg(), null);
    }

    public OrderResult<ArrayList<Order>> queryOrders(OrderInfo qi, String accountId) {
        ArrayList<Order> list = this.orderRepository.findByAccountId(UUID.fromString(accountId));
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
            return new OrderResult(Integer.valueOf(1), "Get order num", finalList);
        }
        LOGGER.warn("[Query Order] Orders don't fit the requirement, loginId: {}", (Object)qi.getLoginId());
        return new OrderResult(Integer.valueOf(1), "Get order num", list);
    }

    @Override
    public OrderResult queryOrdersForRefresh(OrderInfo qi, String accountId) {
        ArrayList<Order> orders = this.queryOrders(qi, accountId).getData();
        ArrayList<String> stationIds = new ArrayList<String>();
        for (Order order : orders) {
            stationIds.add(order.getFrom());
            stationIds.add(order.getTo());
        }
        List<String> names = this.queryForStationId(stationIds);
        for (int i = 0; i < orders.size(); ++i) {
            ((Order)orders.get(i)).setFrom(names.get(i * 2));
            ((Order)orders.get(i)).setTo(names.get(i * 2 + 1));
        }
        return new OrderResult(Integer.valueOf(1), "Query Orders For Refresh Success", (Object)orders);
    }

    @SuppressWarnings("unchecked")
    public List<String> queryForStationId(List<String> ids) {
        return (List<String>) stations.namesForIds(ids).getData();
    }

    @Override
    public OrderResult saveChanges(Order order) {
        Order oldOrder = this.orderRepository.findById(order.getId());
        if (oldOrder == null) {
            LOGGER.error("[Modify Order] Fail.Order not found, OrderId: {}", (Object)order.getId());
            return new OrderResult(Integer.valueOf(0), this.orderNotFound, null);
        }
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
        this.orderRepository.save(oldOrder);
        LOGGER.info("Success.");
        return new OrderResult(Integer.valueOf(1), this.success, (Object)oldOrder);
    }

    @Override
    public OrderResult cancelOrder(UUID accountId, UUID orderId) {
        Order oldOrder = this.orderRepository.findById(orderId);
        if (oldOrder == null) {
            LOGGER.error("[Cancel Order] Fail.Order not found, OrderId: {}", (Object)orderId);
            return new OrderResult(Integer.valueOf(0), this.orderNotFound, null);
        }
        oldOrder.setStatus(OrderStatus.CANCEL.getCode());
        this.orderRepository.save(oldOrder);
        LOGGER.info("[Cancel Order] Success.");
        return new OrderResult(Integer.valueOf(1), this.success, (Object)oldOrder);
    }

    @Override
    public OrderResult queryAlreadySoldOrders(Date travelDate, String trainNumber) {
        ArrayList<Order> orders = this.orderRepository.findByTravelDateAndTrainNumber(travelDate, trainNumber);
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
        return new OrderResult(Integer.valueOf(1), this.success, (Object)cstr);
    }

    @Override
    public OrderResult getAllOrders() {
        List orders = this.orderRepository.findAll();
        if (orders != null && !((ArrayList)orders).isEmpty()) {
            return new OrderResult(Integer.valueOf(1), "Success.", (Object)orders);
        }
        LOGGER.warn("Find all orders warn: {}", (Object)"No content");
        return new OrderResult(Integer.valueOf(0), "No Content.", null);
    }

    @Override
    public OrderResult modifyOrder(String orderId, int status) {
        Order order = this.orderRepository.findById(UUID.fromString(orderId));
        if (order == null) {
            LOGGER.error("Modify order error.Order not found, OrderId: {}", (Object)orderId);
            return new OrderResult(Integer.valueOf(0), this.orderNotFound, null);
        }
        order.setStatus(status);
        this.orderRepository.save(order);
        return new OrderResult(Integer.valueOf(1), "Modify Order Success", (Object)order);
    }

    @Override
    public OrderResult getOrderPrice(String orderId) {
        Order order = this.orderRepository.findById(UUID.fromString(orderId));
        if (order == null) {
            LOGGER.error("Get order price error.Order not found, OrderId: {}", (Object)orderId);
            return new OrderResult(Integer.valueOf(0), this.orderNotFound, (Object)"-1.0");
        }
        LOGGER.info("[Get Order Price] Price: {}", (Object)order.getPrice());
        return new OrderResult(Integer.valueOf(1), this.success, (Object)order.getPrice());
    }

    @Override
    public OrderResult payOrder(String orderId) {
        Order order = this.orderRepository.findById(UUID.fromString(orderId));
        if (order == null) {
            LOGGER.error("Pay order error.Order not found, OrderId: {}", (Object)orderId);
            return new OrderResult(Integer.valueOf(0), this.orderNotFound, null);
        }
        order.setStatus(OrderStatus.PAID.getCode());
        this.orderRepository.save(order);
        return new OrderResult(Integer.valueOf(1), "Pay Order Success.", (Object)order);
    }

    @Override
    public OrderResult getOrderById(String orderId) {
        Order order = this.orderRepository.findById(UUID.fromString(orderId));
        if (order == null) {
            LOGGER.error("Order not found, OrderId: {}", (Object)orderId);
            return new OrderResult(Integer.valueOf(0), this.orderNotFound, null);
        }
        return new OrderResult(Integer.valueOf(1), "Success.", (Object)order);
    }

    @Override
    public void initOrder(Order order) {
        Order orderTemp = this.orderRepository.findById(order.getId());
        if (orderTemp == null) {
            this.orderRepository.save(order);
        } else {
            LOGGER.error("[Init Order] Order Already Exists, OrderId: {}", (Object)order.getId());
        }
    }

    @Override
    public OrderResult checkSecurityAboutOrder(Date dateFrom, String accountId) {
        OrderSecurity result = new OrderSecurity();
        ArrayList<Order> orders = this.orderRepository.findByAccountId(UUID.fromString(accountId));
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
        return new OrderResult(Integer.valueOf(1), "Check Security Success . ", (Object)result);
    }

    @Override
    public OrderResult deleteOrder(String orderId) {
        UUID orderUuid = UUID.fromString(orderId);
        Order order = this.orderRepository.findById(orderUuid);
        if (order == null) {
            LOGGER.error("Delete order error.Order not found, OrderId: {}", (Object)orderId);
            return new OrderResult(Integer.valueOf(0), "Order Not Exist.", null);
        }
        this.orderRepository.deleteById(orderUuid);
        return new OrderResult(Integer.valueOf(1), "Delete Order Success", (Object)order);
    }

    @Override
    public OrderResult addNewOrder(Order order) {
        LOGGER.info("[Admin Add Order] Ready Add Order.");
        ArrayList<Order> accountOrders = this.orderRepository.findByAccountId(order.getAccountId());
        if (accountOrders.contains(order)) {
            LOGGER.error("[Admin Add Order] Fail.Order already exists, OrderId: {}", (Object)order.getId());
            return new OrderResult(Integer.valueOf(0), "Order already exist", null);
        }
        order.setId(UUID.randomUUID());
        this.orderRepository.save(order);
        LOGGER.info("[Admin Add Order] Success.");
        LOGGER.info("[Admin Add Order] Price: {}", (Object)order.getPrice());
        return new OrderResult(Integer.valueOf(1), "Add new Order Success", (Object)order);
    }

    @Override
    public OrderResult updateOrder(Order order) {
        LOGGER.info("UPDATE ORDER INFO: " + order.toString());
        Order oldOrder = this.orderRepository.findById(order.getId());
        if (oldOrder == null) {
            LOGGER.error("[Admin Update Order] Fail.Order not found, OrderId: {}", (Object)order.getId());
            return new OrderResult(Integer.valueOf(0), "Order Not Found, Can't update", null);
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
        this.orderRepository.save(oldOrder);
        LOGGER.info("[Admin Update Order] Success.");
        return new OrderResult(Integer.valueOf(1), "Admin Update Order Success", (Object)oldOrder);
    }
}

