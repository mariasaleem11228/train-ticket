package trainticket.orderother;

import java.util.Date;
import java.util.UUID;
import trainticket.orderother.Order;
import trainticket.orderother.OrderAlterInfo;
import trainticket.orderother.QueryInfo;
import trainticket.orderother.Seat;

public interface OrderOtherOperations {
    public OrderOtherResult findOrderById(UUID var1);

    public OrderOtherResult create(Order var1);

    public OrderOtherResult updateOrder(Order var1);

    public OrderOtherResult saveChanges(Order var1);

    public OrderOtherResult cancelOrder(UUID var1, UUID var2);

    public OrderOtherResult addNewOrder(Order var1);

    public OrderOtherResult deleteOrder(String var1);

    public OrderOtherResult getOrderById(String var1);

    public OrderOtherResult payOrder(String var1);

    public OrderOtherResult getOrderPrice(String var1);

    public OrderOtherResult modifyOrder(String var1, int var2);

    public OrderOtherResult getAllOrders();

    public OrderOtherResult getSoldTickets(Seat var1);

    public OrderOtherResult queryOrders(QueryInfo var1, String var2);

    public OrderOtherResult queryOrdersForRefresh(QueryInfo var1, String var2);

    public OrderOtherResult alterOrder(OrderAlterInfo var1);

    public OrderOtherResult queryAlreadySoldOrders(Date var1, String var2);

    public OrderOtherResult checkSecurityAboutOrder(Date var1, String var2);

    public void initOrder(Order var1);
}

