/* Ported from the deployed codewisdom/ts-order-service:0.2.0 classes.
 * Preserve benchmark behaviour; see docs/migration/orders-pilot-results.md. */
package trainticket.orders;


import java.util.Date;
import java.util.UUID;
import trainticket.orders.Order;
import trainticket.orders.OrderAlterInfo;
import trainticket.orders.OrderInfo;
import trainticket.orders.Seat;

public interface OrderOperations {
    public OrderResult findOrderById(UUID var1);

    public OrderResult create(Order var1);

    /** Insert the supplied ID once; retries return the existing order. */
    public OrderResult createIfAbsent(Order order);

    public OrderResult saveChanges(Order var1);

    public OrderResult cancelOrder(UUID var1, UUID var2);

    public OrderResult queryOrders(OrderInfo var1, String var2);

    public OrderResult queryOrdersForRefresh(OrderInfo var1, String var2);

    public OrderResult alterOrder(OrderAlterInfo var1);

    public OrderResult queryAlreadySoldOrders(Date var1, String var2);

    public OrderResult getAllOrders();

    public OrderResult modifyOrder(String var1, int var2);

    public OrderResult getOrderPrice(String var1);

    public OrderResult payOrder(String var1);

    public OrderResult getOrderById(String var1);

    public OrderResult checkSecurityAboutOrder(Date var1, String var2);

    public void initOrder(Order var1);

    public OrderResult deleteOrder(String var1);

    public OrderResult getSoldTickets(Seat var1);

    public OrderResult addNewOrder(Order var1);

    public OrderResult updateOrder(Order var1);
}

