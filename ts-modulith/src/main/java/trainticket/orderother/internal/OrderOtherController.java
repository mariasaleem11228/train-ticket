/* Deployed 0.2.0 OrderOther HTTP contract. */
package trainticket.orderother.internal;

import java.util.Date;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import trainticket.orderother.Order;
import trainticket.orderother.QueryInfo;
import trainticket.orderother.Seat;
import trainticket.orderother.OrderOtherOperations;

@RestController
@org.springframework.boot.autoconfigure.condition.ConditionalOnProperty(name="modulith.order-other.enabled", havingValue="true")
@RequestMapping(value={"/api/v1/orderOtherService"})
public class OrderOtherController {
    @Autowired
    private OrderOtherOperations orderService;
    private static final Logger LOGGER = LoggerFactory.getLogger(OrderOtherController.class);

    @GetMapping(path={"/welcome"})
    public String home() {
        return "Welcome to [ Order Other Service ] !";
    }

    @PostMapping(value={"/orderOther/tickets"})
    public HttpEntity getTicketListByDateAndTripId(@RequestBody Seat seatRequest) {
        LOGGER.info("[Get Sold Ticket] Date: {}", (Object)seatRequest.getTravelDate().toString());
        return ResponseEntity.ok((Object)this.orderService.getSoldTickets(seatRequest));
    }

    @CrossOrigin(origins={"*"})
    @PostMapping(path={"/orderOther"})
    public HttpEntity createNewOrder(@RequestBody Order createOrder) {
        LOGGER.info("[Create Order] Create Order form {}  ---> {} at {}", new Object[]{createOrder.getFrom(), createOrder.getTo(), createOrder.getTravelDate()});
        LOGGER.info("[Verify Login] Success");
        return ResponseEntity.ok((Object)this.orderService.create(createOrder));
    }

    @CrossOrigin(origins={"*"})
    @PostMapping(path={"/orderOther/admin"})
    public HttpEntity addcreateNewOrder(@RequestBody Order order) {
        LOGGER.info("Add new order, OrderId: {}", (Object)order.getId());
        return ResponseEntity.ok((Object)this.orderService.addNewOrder(order));
    }

    @CrossOrigin(origins={"*"})
    @PostMapping(path={"/orderOther/query"})
    public HttpEntity queryOrders(@RequestBody QueryInfo qi) {
        LOGGER.info("[Query Orders] Query Orders for {}", (Object)qi.getLoginId());
        return ResponseEntity.ok((Object)this.orderService.queryOrders(qi, qi.getLoginId()));
    }

    @CrossOrigin(origins={"*"})
    @PostMapping(path={"/orderOther/refresh"})
    public HttpEntity queryOrdersForRefresh(@RequestBody QueryInfo qi) {
        LOGGER.info("[Query Orders] Query Orders for {}", (Object)qi.getLoginId());
        return ResponseEntity.ok((Object)this.orderService.queryOrdersForRefresh(qi, qi.getLoginId()));
    }

    @CrossOrigin(origins={"*"})
    @GetMapping(path={"/orderOther/{travelDate}/{trainNumber}"})
    public HttpEntity calculateSoldTicket(@PathVariable Date travelDate, @PathVariable String trainNumber) {
        LOGGER.info("[Calculate Sold Tickets] Date: {} TrainNumber: {}", (Object)travelDate, (Object)trainNumber);
        return ResponseEntity.ok((Object)this.orderService.queryAlreadySoldOrders(travelDate, trainNumber));
    }

    @CrossOrigin(origins={"*"})
    @GetMapping(path={"/orderOther/price/{orderId}"})
    public HttpEntity getOrderPrice(@PathVariable String orderId) {
        LOGGER.info("[Get Order Price] Order Id: {}", (Object)orderId);
        return ResponseEntity.ok((Object)this.orderService.getOrderPrice(orderId));
    }

    @CrossOrigin(origins={"*"})
    @GetMapping(path={"/orderOther/orderPay/{orderId}"})
    public HttpEntity payOrder(@PathVariable String orderId) {
        LOGGER.info("[Pay Order] Order Id: {}", (Object)orderId);
        return ResponseEntity.ok((Object)this.orderService.payOrder(orderId));
    }

    @CrossOrigin(origins={"*"})
    @GetMapping(path={"/orderOther/{orderId}"})
    public HttpEntity getOrderById(@PathVariable String orderId) {
        LOGGER.info("[Get Order By Id] Order Id: {}", (Object)orderId);
        return ResponseEntity.ok((Object)this.orderService.getOrderById(orderId));
    }

    @CrossOrigin(origins={"*"})
    @GetMapping(path={"/orderOther/status/{orderId}/{status}"})
    public HttpEntity modifyOrder(@PathVariable String orderId, @PathVariable int status) {
        LOGGER.info("[Modify Order Status] Order Id: {}", (Object)orderId);
        return ResponseEntity.ok((Object)this.orderService.modifyOrder(orderId, status));
    }

    @CrossOrigin(origins={"*"})
    @GetMapping(path={"/orderOther/security/{checkDate}/{accountId}"})
    public HttpEntity securityInfoCheck(@PathVariable Date checkDate, @PathVariable String accountId) {
        LOGGER.info("[Security Info Get]");
        return ResponseEntity.ok((Object)this.orderService.checkSecurityAboutOrder(checkDate, accountId));
    }

    @CrossOrigin(origins={"*"})
    @PutMapping(path={"/orderOther"})
    public HttpEntity saveOrderInfo(@RequestBody Order orderInfo) {
        LOGGER.info("[Verify Login] Success");
        return ResponseEntity.ok((Object)this.orderService.saveChanges(orderInfo));
    }

    @CrossOrigin(origins={"*"})
    @PutMapping(path={"/orderOther/admin"})
    public HttpEntity updateOrder(@RequestBody Order order) {
        LOGGER.info("Update Order, OrderId: {}", (Object)order.getId());
        return ResponseEntity.ok((Object)this.orderService.updateOrder(order));
    }

    @CrossOrigin(origins={"*"})
    @DeleteMapping(path={"/orderOther/{orderId}"})
    public HttpEntity deleteOrder(@PathVariable String orderId) {
        LOGGER.info("[Delete Order] Order Id: {}", (Object)orderId);
        return ResponseEntity.ok((Object)this.orderService.deleteOrder(orderId));
    }

    @CrossOrigin(origins={"*"})
    @GetMapping(path={"/orderOther"})
    public HttpEntity findAllOrder() {
        LOGGER.info("[Find All Order]");
        return ResponseEntity.ok((Object)this.orderService.getAllOrders());
    }
}

