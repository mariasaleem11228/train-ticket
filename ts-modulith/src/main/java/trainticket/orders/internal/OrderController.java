/* Ported from the deployed codewisdom/ts-order-service:0.2.0 classes.
 * Preserve benchmark behaviour; see docs/migration/orders-pilot-results.md. */
package trainticket.orders.internal;

import java.util.Date;
import trainticket.orders.Order;
import trainticket.orders.OrderInfo;
import trainticket.orders.Seat;
import trainticket.orders.OrderOperations;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@org.springframework.boot.autoconfigure.condition.ConditionalOnProperty(name="modulith.orders.enabled", havingValue="true")
@RequestMapping(value={"/api/v1/orderservice"})
public class OrderController {
    @Autowired
    private OrderOperations orderService;
    private static final Logger LOGGER = LoggerFactory.getLogger(OrderController.class);

    @GetMapping(path={"/welcome"})
    public String home() {
        return "Welcome to [ Order Service ] !";
    }

    @PostMapping(value={"/order/tickets"})
    public HttpEntity getTicketListByDateAndTripId(@RequestBody Seat seatRequest, @RequestHeader HttpHeaders headers) {
        LOGGER.info("[Get Sold Ticket] Date: {}", (Object)seatRequest.getTravelDate().toString());
        return ResponseEntity.ok((Object)this.orderService.getSoldTickets(seatRequest));
    }

    @CrossOrigin(origins={"*"})
    @PostMapping(path={"/order"})
    public HttpEntity createNewOrder(@RequestBody Order createOrder, @RequestHeader HttpHeaders headers) {
        LOGGER.info("[Create Order] Create Order form {} ---> {} at {}", new Object[]{createOrder.getFrom(), createOrder.getTo(), createOrder.getTravelDate()});
        LOGGER.info("[Verify Login] Success");
        return ResponseEntity.ok((Object)this.orderService.create(createOrder));
    }

    @CrossOrigin(origins={"*"})
    @PostMapping(path={"/order/admin"})
    public HttpEntity addcreateNewOrder(@RequestBody Order order, @RequestHeader HttpHeaders headers) {
        return ResponseEntity.ok((Object)this.orderService.addNewOrder(order));
    }

    @CrossOrigin(origins={"*"})
    @PostMapping(path={"/order/query"})
    public HttpEntity queryOrders(@RequestBody OrderInfo qi, @RequestHeader HttpHeaders headers) {
        LOGGER.info("[Query Orders] Query Orders for {}", (Object)qi.getLoginId());
        LOGGER.info("[Verify Login] Success");
        return ResponseEntity.ok((Object)this.orderService.queryOrders(qi, qi.getLoginId()));
    }

    @CrossOrigin(origins={"*"})
    @PostMapping(path={"/order/refresh"})
    public HttpEntity queryOrdersForRefresh(@RequestBody OrderInfo qi, @RequestHeader HttpHeaders headers) {
        LOGGER.info("[Query Orders] Query Orders for {}", (Object)qi.getLoginId());
        return ResponseEntity.ok((Object)this.orderService.queryOrdersForRefresh(qi, qi.getLoginId()));
    }

    @CrossOrigin(origins={"*"})
    @GetMapping(path={"/order/{travelDate}/{trainNumber}"})
    public HttpEntity calculateSoldTicket(@PathVariable Date travelDate, @PathVariable String trainNumber, @RequestHeader HttpHeaders headers) {
        LOGGER.info("[Calculate Sold Tickets] Date: {} TrainNumber: {}", (Object)travelDate, (Object)trainNumber);
        return ResponseEntity.ok((Object)this.orderService.queryAlreadySoldOrders(travelDate, trainNumber));
    }

    @CrossOrigin(origins={"*"})
    @GetMapping(path={"/order/price/{orderId}"})
    public HttpEntity getOrderPrice(@PathVariable String orderId, @RequestHeader HttpHeaders headers) {
        LOGGER.info("[Get Order Price] Order Id: {}", (Object)orderId);
        return ResponseEntity.ok((Object)this.orderService.getOrderPrice(orderId));
    }

    @CrossOrigin(origins={"*"})
    @GetMapping(path={"/order/orderPay/{orderId}"})
    public HttpEntity payOrder(@PathVariable String orderId, @RequestHeader HttpHeaders headers) {
        LOGGER.info("[Pay Order] Order Id: {}", (Object)orderId);
        return ResponseEntity.ok((Object)this.orderService.payOrder(orderId));
    }

    @CrossOrigin(origins={"*"})
    @GetMapping(path={"/order/{orderId}"})
    public HttpEntity getOrderById(@PathVariable String orderId, @RequestHeader HttpHeaders headers) {
        LOGGER.info("[Get Order By Id] Order Id: {}", (Object)orderId);
        return ResponseEntity.ok((Object)this.orderService.getOrderById(orderId));
    }

    @CrossOrigin(origins={"*"})
    @GetMapping(path={"/order/status/{orderId}/{status}"})
    public HttpEntity modifyOrder(@PathVariable String orderId, @PathVariable int status, @RequestHeader HttpHeaders headers) {
        LOGGER.info("[Modify Order Status] Order Id: {}", (Object)orderId);
        return ResponseEntity.ok((Object)this.orderService.modifyOrder(orderId, status));
    }

    @CrossOrigin(origins={"*"})
    @GetMapping(path={"/order/security/{checkDate}/{accountId}"})
    public HttpEntity securityInfoCheck(@PathVariable Date checkDate, @PathVariable String accountId, @RequestHeader HttpHeaders headers) {
        LOGGER.info("[Security Info Get] {}", (Object)accountId);
        return ResponseEntity.ok((Object)this.orderService.checkSecurityAboutOrder(checkDate, accountId));
    }

    @CrossOrigin(origins={"*"})
    @PutMapping(path={"/order"})
    public HttpEntity saveOrderInfo(@RequestBody Order orderInfo, @RequestHeader HttpHeaders headers) {
        LOGGER.info("[Verify Login] Success");
        return ResponseEntity.ok((Object)this.orderService.saveChanges(orderInfo));
    }

    @CrossOrigin(origins={"*"})
    @PutMapping(path={"/order/admin"})
    public HttpEntity updateOrder(@RequestBody Order order, @RequestHeader HttpHeaders headers) {
        LOGGER.info("Update Order, OrderId: {}", (Object)order.getId());
        return ResponseEntity.ok((Object)this.orderService.updateOrder(order));
    }

    @CrossOrigin(origins={"*"})
    @DeleteMapping(path={"/order/{orderId}"})
    public HttpEntity deleteOrder(@PathVariable String orderId, @RequestHeader HttpHeaders headers) {
        LOGGER.info("[Delete Order] Order Id: {}", (Object)orderId);
        return ResponseEntity.ok((Object)this.orderService.deleteOrder(orderId));
    }

    @CrossOrigin(origins={"*"})
    @GetMapping(path={"/order"})
    public HttpEntity findAllOrder(@RequestHeader HttpHeaders headers) {
        LOGGER.info("[Find All Order]");
        return ResponseEntity.ok((Object)this.orderService.getAllOrders());
    }
}

