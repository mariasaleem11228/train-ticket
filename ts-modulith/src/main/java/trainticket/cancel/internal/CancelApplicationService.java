package trainticket.cancel.internal;

import com.fasterxml.jackson.databind.JsonNode;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;
import trainticket.cancel.CancelOperations;
import trainticket.cancel.CancelResult;
import trainticket.insidepayment.InsidePaymentOperations;
import trainticket.insidepayment.InsidePaymentResult;
import trainticket.orderother.OrderOtherOperations;
import trainticket.orderother.OrderOtherResult;
import trainticket.orders.OrderOperations;
import trainticket.orders.OrderResult;
import trainticket.runtime.WriteOwnership;
import java.text.DecimalFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.Objects;

/** Keeps the deployed cancel/refund responses and calls local business APIs. */
@Service
@ConditionalOnProperty(name="modulith.cancel.enabled",havingValue="true")
class CancelApplicationService implements CancelOperations {
    private static final String NOT_PERMITTED="Order Status Cancel Not Permitted";
    private final OrderOperations orders;
    private final OrderOtherOperations otherOrders;
    private final InsidePaymentOperations wallet;
    private final CancelRemoteUser user;
    private final WriteOwnership ownership;
    private final boolean writesEnabled;
    CancelApplicationService(OrderOperations orders,OrderOtherOperations otherOrders,
                             InsidePaymentOperations wallet,CancelRemoteUser user,
                             WriteOwnership ownership,
                             @Value("${modulith.cancel.writes-enabled:false}") boolean writesEnabled) {
        this.orders=orders;this.otherOrders=otherOrders;this.wallet=wallet;this.user=user;
        this.ownership=ownership;this.writesEnabled=writesEnabled;
    }

    @Override public CancelResult<?> refund(String orderId) {
        OrderResult<?> standard=orders.getOrderById(orderId);
        if(standard.getStatus()==1) {
            trainticket.orders.Order order=(trainticket.orders.Order)standard.getData();
            if(order.getStatus()==0)return new CancelResult<>(1,"Success. Refoud 0","0");
            if(order.getStatus()==1)return new CancelResult<>(1,"Success. ",amount(order.getStatus(),
                    order.getTravelDate(),order.getTravelTime(),order.getPrice()));
            return result(0,"Order Status Cancel Not Permitted, Refound error");
        }
        OrderOtherResult<?> other=otherOrders.getOrderById(orderId);
        if(other.getStatus()!=1)return result(0,"Order Not Found");
        trainticket.orderother.Order order=(trainticket.orderother.Order)other.getData();
        if(order.getStatus()==0)return new CancelResult<>(1,"Success, Refound 0","0");
        if(order.getStatus()==1)return new CancelResult<>(1,"Success",amount(order.getStatus(),
                order.getTravelDate(),order.getTravelTime(),order.getPrice()));
        return result(0,NOT_PERMITTED);
    }

    @Override public CancelResult<?> cancel(String orderId,String loginId,String authorization) {
        requireWriter();
        OrderResult<?> standard=orders.getOrderById(orderId);
        if(standard.getStatus()==1) {
            trainticket.orders.Order order=(trainticket.orders.Order)standard.getData();
            if(!cancellable(order.getStatus()))return result(0,NOT_PERMITTED);
            order.setStatus(4);
            OrderResult<?> changed=orders.saveChanges(order);
            if(changed.getStatus()!=1)return result(0,changed.getMsg());
            String refund=amount(order.getStatus(),order.getTravelDate(),order.getTravelTime(),order.getPrice());
            InsidePaymentResult<?> drawback=wallet.drawBack(loginId,refund);
            if(drawback.status()==1) {
                JsonNode account=user.get(order.getAccountId().toString(),authorization);
                if(account.path("status").asInt()==0)return result(0,"Cann't find userinfo by user id.");
                // The deployed service builds notification data but does not send it.
                Objects.requireNonNull(order.getTravelTime()).toString();
            }
            return new CancelResult<>(1,"Success.","test not null");
        }
        OrderOtherResult<?> other=otherOrders.getOrderById(orderId);
        if(other.getStatus()!=1)return result(0,"Order Not Found.");
        trainticket.orderother.Order order=(trainticket.orderother.Order)other.getData();
        if(!cancellable(order.getStatus()))return result(0,NOT_PERMITTED);
        order.setStatus(4);
        OrderOtherResult<?> changed=otherOrders.saveChanges(order);
        if(changed.getStatus()!=1)return result(0,"Fail.Reason:"+changed.getMsg());
        String refund=amount(order.getStatus(),order.getTravelDate(),order.getTravelTime(),order.getPrice());
        wallet.drawBack(loginId,refund);
        return result(1,"Success.");
    }
    private boolean cancellable(int status) { return status==0||status==1||status==3; }
    private void requireWriter() {
        if(!writesEnabled||!ownership.permits("cancel"))
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,"Cancel writes disabled");
    }
    private CancelResult<?> result(int status,String message) {
        return new CancelResult<>(status,message,null);
    }
    @SuppressWarnings("deprecation")
    private String amount(int status,Date travelDate,Date travelTime,String price) {
        if(status==0)return "0.00";
        Calendar day=Calendar.getInstance();day.setTime(travelDate);
        Calendar clock=Calendar.getInstance();clock.setTime(travelTime);
        // The deployed image uses Date(year, month, day, Calendar.HOUR, ...).
        Date departure=new Date(day.get(Calendar.YEAR),day.get(Calendar.MONTH),
                day.get(Calendar.DAY_OF_MONTH),clock.get(Calendar.HOUR),
                clock.get(Calendar.MINUTE),clock.get(Calendar.SECOND));
        if(new Date().after(departure))return "0";
        return new DecimalFormat("0.00").format(Double.parseDouble(price)*0.8);
    }
}
