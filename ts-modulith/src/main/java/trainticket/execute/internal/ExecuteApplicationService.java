package trainticket.execute.internal;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;
import trainticket.execute.ExecuteOperations;
import trainticket.execute.ExecuteResult;
import trainticket.orderother.OrderOtherOperations;
import trainticket.orderother.OrderOtherResult;
import trainticket.orders.OrderOperations;
import trainticket.orders.OrderResult;
import trainticket.runtime.WriteOwnership;

/** Implements the deployed Execute status transitions through the two published order APIs. */
@Service
@ConditionalOnProperty(name="modulith.execute.enabled", havingValue="true")
class ExecuteApplicationService implements ExecuteOperations {
    private final OrderOperations orders;
    private final OrderOtherOperations other;
    private final WriteOwnership ownership;
    private final boolean writesEnabled;

    ExecuteApplicationService(OrderOperations orders, OrderOtherOperations other,
                              WriteOwnership ownership,
                              @Value("${modulith.execute.writes-enabled:false}") boolean writesEnabled) {
        this.orders=orders; this.other=other; this.ownership=ownership;
        this.writesEnabled=writesEnabled;
    }

    @Override public ExecuteResult execute(String id) { return change(id, 2, 6, true); }
    @Override public ExecuteResult collect(String id) { return change(id, 1, 2, false); }

    private ExecuteResult change(String id, int requiredStatus, int targetStatus, boolean executing) {
        // Both legacy GET endpoints mutate order state. Fence before calling either order module.
        if (!writesEnabled || !ownership.permits("execute"))
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE, "Execute writes disabled");

        OrderResult<?> found=orders.getOrderById(id);
        if (found.getStatus()==1) {
            trainticket.orders.Order order=(trainticket.orders.Order)found.getData();
            if (!allowed(order.getStatus(),requiredStatus,executing)) return fail("Order Status Wrong");
            OrderResult<?> changed=orders.modifyOrder(id,targetStatus);
            return changed.getStatus()==1 ? ok(executing ? "Success." : "Success") : fail(changed.getMsg());
        }
        OrderOtherResult<?> otherFound=other.getOrderById(id);
        if (otherFound.getStatus()!=1) return fail("Order Not Found");
        trainticket.orderother.Order order=(trainticket.orderother.Order)otherFound.getData();
        if (!allowed(order.getStatus(),requiredStatus,executing)) return fail("Order Status Wrong");
        OrderOtherResult<?> changed=other.modifyOrder(id,targetStatus);
        return changed.getStatus()==1 ? ok(executing ? "Success" : "Success.") : fail(changed.getMsg());
    }

    private boolean allowed(int status,int required,boolean executing) {
        return status==required || (!executing && status==3);
    }
    private ExecuteResult ok(String message) { return new ExecuteResult(1,message,null); }
    private ExecuteResult fail(String message) { return new ExecuteResult(0,message,null); }
}
