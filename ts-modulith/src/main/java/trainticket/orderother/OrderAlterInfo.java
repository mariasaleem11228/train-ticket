/* Deployed codewisdom OrderOther 0.2.0 DTO. */
package trainticket.orderother;

import java.util.UUID;
import trainticket.orderother.Order;

public class OrderAlterInfo {
    private UUID accountId;
    private UUID previousOrderId;
    private String loginToken;
    private Order newOrderInfo;

    public OrderAlterInfo() {
        this.newOrderInfo = new Order();
    }

    public UUID getAccountId() {
        return this.accountId;
    }

    public UUID getPreviousOrderId() {
        return this.previousOrderId;
    }

    public String getLoginToken() {
        return this.loginToken;
    }

    public Order getNewOrderInfo() {
        return this.newOrderInfo;
    }

    public void setAccountId(UUID accountId) {
        this.accountId = accountId;
    }

    public void setPreviousOrderId(UUID previousOrderId) {
        this.previousOrderId = previousOrderId;
    }

    public void setLoginToken(String loginToken) {
        this.loginToken = loginToken;
    }

    public void setNewOrderInfo(Order newOrderInfo) {
        this.newOrderInfo = newOrderInfo;
    }

    public boolean equals(Object o) {
        if (o == this) {
            return true;
        }
        if (!(o instanceof OrderAlterInfo)) {
            return false;
        }
        OrderAlterInfo other = (OrderAlterInfo)o;
        if (!other.canEqual((Object)this)) {
            return false;
        }
        UUID this$accountId = this.getAccountId();
        UUID other$accountId = other.getAccountId();
        if (this$accountId == null ? other$accountId != null : !((Object)this$accountId).equals(other$accountId)) {
            return false;
        }
        UUID this$previousOrderId = this.getPreviousOrderId();
        UUID other$previousOrderId = other.getPreviousOrderId();
        if (this$previousOrderId == null ? other$previousOrderId != null : !((Object)this$previousOrderId).equals(other$previousOrderId)) {
            return false;
        }
        String this$loginToken = this.getLoginToken();
        String other$loginToken = other.getLoginToken();
        if (this$loginToken == null ? other$loginToken != null : !this$loginToken.equals(other$loginToken)) {
            return false;
        }
        Order this$newOrderInfo = this.getNewOrderInfo();
        Order other$newOrderInfo = other.getNewOrderInfo();
        return !(this$newOrderInfo == null ? other$newOrderInfo != null : !this$newOrderInfo.equals(other$newOrderInfo));
    }

    protected boolean canEqual(Object other) {
        return other instanceof OrderAlterInfo;
    }

    public int hashCode() {
        int PRIME = 59;
        int result = 1;
        UUID $accountId = this.getAccountId();
        result = result * 59 + ($accountId == null ? 43 : ((Object)$accountId).hashCode());
        UUID $previousOrderId = this.getPreviousOrderId();
        result = result * 59 + ($previousOrderId == null ? 43 : ((Object)$previousOrderId).hashCode());
        String $loginToken = this.getLoginToken();
        result = result * 59 + ($loginToken == null ? 43 : $loginToken.hashCode());
        Order $newOrderInfo = this.getNewOrderInfo();
        result = result * 59 + ($newOrderInfo == null ? 43 : $newOrderInfo.hashCode());
        return result;
    }

    public String toString() {
        return "OrderAlterInfo(accountId=" + this.getAccountId() + ", previousOrderId=" + this.getPreviousOrderId() + ", loginToken=" + this.getLoginToken() + ", newOrderInfo=" + this.getNewOrderInfo() + ")";
    }

    public OrderAlterInfo(UUID accountId, UUID previousOrderId, String loginToken, Order newOrderInfo) {
        this.accountId = accountId;
        this.previousOrderId = previousOrderId;
        this.loginToken = loginToken;
        this.newOrderInfo = newOrderInfo;
    }
}

