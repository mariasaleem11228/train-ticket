package trainticket.insidepayment.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import trainticket.insidepayment.*;
import trainticket.orderother.OrderOtherOperations;
import trainticket.orderother.OrderOtherResult;
import trainticket.orders.OrderOperations;
import trainticket.orders.OrderResult;
import trainticket.payment.PaymentOperations;
import trainticket.payment.PaymentRequest;
import trainticket.payment.PaymentResult;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/** Preserves the deployed wallet rules while calling local order and payment APIs. */
@Service
@ConditionalOnProperty(name="modulith.inside-payment.enabled",havingValue="true")
class InsidePaymentApplicationService implements InsidePaymentOperations {
    private final WalletRepository wallet;
    private final OrderOperations orders;
    private final OrderOtherOperations otherOrders;
    private final PaymentOperations outside;

    InsidePaymentApplicationService(WalletRepository wallet,OrderOperations orders,
                                    OrderOtherOperations otherOrders,PaymentOperations outside) {
        this.wallet=wallet;this.orders=orders;this.otherOrders=otherOrders;this.outside=outside;
    }

    @Override public InsidePaymentResult<?> pay(InsidePaymentRequest info) {
        wallet.requireWriter();
        OrderState order=findOrder(info.tripId(),info.orderId());
        if(order.status()!=1)return result(0,"Payment Failed, Order Not Exists");
        if(order.orderStatus()!=0)return result(0,"Error. Order status Not allowed to Pay.");
        BigDecimal spent=spent(info.userId()).add(new BigDecimal(order.price()));
        BigDecimal funds=funds(info.userId());
        if(spent.compareTo(funds)>0) {
            PaymentResult<?> paid=outside.pay(new PaymentRequest(null,info.orderId(),info.userId(),order.price()));
            if(paid.status()!=1)return result(0,"Payment Failed:  "+paid.msg());
            wallet.save(payment(info.orderId(),info.userId(),order.price(),"O"));
            markPaid(info.tripId(),info.orderId());
            return result(1,"Payment Success "+paid.msg());
        }
        markPaid(info.tripId(),info.orderId());
        wallet.save(payment(info.orderId(),info.userId(),order.price(),"P"));
        return result(1,"Payment Success");
    }
    @Override public InsidePaymentResult<?> createAccount(AccountRequest info) {
        wallet.requireWriter();
        if(!wallet.moniesFor(info.userId()).isEmpty())
            return result(0,"Create Account Failed, Account already Exists");
        wallet.save(money(info.userId(),info.money(),"A"));
        return result(1,"Create Account Success");
    }
    @Override public InsidePaymentResult<?> addMoney(String userId,String money) {
        wallet.requireWriter();
        // The deployed repository returns a list, including an empty list, so this always saves.
        wallet.save(money(userId,money,"A"));
        return result(1,"Add Money Success");
    }
    @Override public InsidePaymentResult<List<WalletBalance>> queryAccount() {
        Map<String,String> totals=new HashMap<>();
        for(WalletMoney row:wallet.monies()) {
            String previous=totals.get(row.userId());
            totals.put(row.userId(),previous==null?row.money():
                    new BigDecimal(previous).add(new BigDecimal(row.money())).toString());
        }
        List<WalletBalance> balances=new ArrayList<>();
        for(var entry:totals.entrySet())
            balances.add(new WalletBalance(entry.getKey(),new BigDecimal(entry.getValue())
                    .subtract(spent(entry.getKey())).toString()));
        return new InsidePaymentResult<>(1,"Success",balances);
    }
    @Override public InsidePaymentResult<List<WalletPayment>> queryPayment() {
        List<WalletPayment> rows=wallet.payments();
        return rows.isEmpty()?new InsidePaymentResult<>(0,"Query Payment Failed",null)
                :new InsidePaymentResult<>(1,"Query Payment Success",rows);
    }
    @Override public InsidePaymentResult<?> drawBack(String userId,String money) {
        wallet.requireWriter();
        wallet.save(money(userId,money,"D"));
        return result(1,"Draw Back Money Success");
    }
    @Override public InsidePaymentResult<?> payDifference(InsidePaymentRequest info) {
        wallet.requireWriter();
        // Deployed code discards both BigDecimal.add results here. Preserve that
        // behavior at the compatibility stage; it therefore records type E locally.
        wallet.save(payment(info.orderId(),info.userId(),info.price(),"E"));
        return result(1,"Pay Difference Success");
    }
    @Override public InsidePaymentResult<?> queryAddMoney() {
        return wallet.monies().isEmpty()?result(0,"Query money failed"):
                result(1,"Query Money Success");
    }
    private OrderState findOrder(String tripId,String orderId) {
        if(standard(tripId)) {
            OrderResult<?> found=orders.getOrderById(orderId);
            if(found.getStatus()!=1)return new OrderState(found.getStatus(),0,null);
            trainticket.orders.Order order=(trainticket.orders.Order)found.getData();
            return new OrderState(1,order.getStatus(),order.getPrice());
        }
        OrderOtherResult<?> found=otherOrders.getOrderById(orderId);
        if(found.getStatus()!=1)return new OrderState(found.getStatus(),0,null);
        trainticket.orderother.Order order=(trainticket.orderother.Order)found.getData();
        return new OrderState(1,order.getStatus(),order.getPrice());
    }
    private void markPaid(String tripId,String orderId) {
        if(standard(tripId))orders.modifyOrder(orderId,1);
        else otherOrders.modifyOrder(orderId,1);
    }
    private boolean standard(String tripId) { return tripId.startsWith("G")||tripId.startsWith("D"); }
    private BigDecimal spent(String userId) {
        BigDecimal total=BigDecimal.ZERO;
        for(WalletPayment row:wallet.paymentsFor(userId))total=total.add(new BigDecimal(row.price()));
        return total;
    }
    private BigDecimal funds(String userId) {
        BigDecimal total=BigDecimal.ZERO;
        for(WalletMoney row:wallet.moniesFor(userId))total=total.add(new BigDecimal(row.money()));
        return total;
    }
    private WalletPayment payment(String orderId,String userId,String price,String type) {
        String id=UUID.randomUUID().toString().replace("-","").toUpperCase();
        return new WalletPayment(id,orderId,userId,price,type);
    }
    private WalletMoney money(String userId,String value,String type) {
        return new WalletMoney(UUID.randomUUID().toString(),userId,value,type);
    }
    private InsidePaymentResult<?> result(int status,String message) {
        return new InsidePaymentResult<>(status,message,null);
    }
    private record OrderState(int status,int orderStatus,String price) {}
}
