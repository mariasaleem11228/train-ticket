/* Deployed codewisdom OrderOther 0.2.0 DTO. */
package trainticket.orderother;

import java.util.Date;

public class QueryInfo {
    private String loginId;
    private Date travelDateStart;
    private Date travelDateEnd;
    private Date boughtDateStart;
    private Date boughtDateEnd;
    private int state;
    private boolean enableTravelDateQuery;
    private boolean enableBoughtDateQuery;
    private boolean enableStateQuery;

    public void enableTravelDateQuery(Date startTime, Date endTime) {
        this.enableTravelDateQuery = true;
        this.travelDateStart = startTime;
        this.travelDateEnd = endTime;
    }

    public void disableTravelDateQuery() {
        this.enableTravelDateQuery = false;
        this.travelDateStart = null;
        this.travelDateEnd = null;
    }

    public void enableBoughtDateQuery(Date startTime, Date endTime) {
        this.enableBoughtDateQuery = true;
        this.boughtDateStart = startTime;
        this.boughtDateEnd = endTime;
    }

    public void disableBoughtDateQuery() {
        this.enableBoughtDateQuery = false;
        this.boughtDateStart = null;
        this.boughtDateEnd = null;
    }

    public void enableStateQuery(int targetStatus) {
        this.enableStateQuery = true;
        this.state = targetStatus;
    }

    public void disableStateQuery() {
        this.enableTravelDateQuery = false;
        this.state = -1;
    }

    public boolean isEnableTravelDateQuery() {
        return this.enableTravelDateQuery;
    }

    public boolean isEnableBoughtDateQuery() {
        return this.enableBoughtDateQuery;
    }

    public boolean isEnableStateQuery() {
        return this.enableStateQuery;
    }

    public String getLoginId() {
        return this.loginId;
    }

    public Date getTravelDateStart() {
        return this.travelDateStart;
    }

    public Date getTravelDateEnd() {
        return this.travelDateEnd;
    }

    public Date getBoughtDateStart() {
        return this.boughtDateStart;
    }

    public Date getBoughtDateEnd() {
        return this.boughtDateEnd;
    }

    public int getState() {
        return this.state;
    }

    public void setLoginId(String loginId) {
        this.loginId = loginId;
    }

    public void setTravelDateStart(Date travelDateStart) {
        this.travelDateStart = travelDateStart;
    }

    public void setTravelDateEnd(Date travelDateEnd) {
        this.travelDateEnd = travelDateEnd;
    }

    public void setBoughtDateStart(Date boughtDateStart) {
        this.boughtDateStart = boughtDateStart;
    }

    public void setBoughtDateEnd(Date boughtDateEnd) {
        this.boughtDateEnd = boughtDateEnd;
    }

    public void setState(int state) {
        this.state = state;
    }

    public void setEnableTravelDateQuery(boolean enableTravelDateQuery) {
        this.enableTravelDateQuery = enableTravelDateQuery;
    }

    public void setEnableBoughtDateQuery(boolean enableBoughtDateQuery) {
        this.enableBoughtDateQuery = enableBoughtDateQuery;
    }

    public void setEnableStateQuery(boolean enableStateQuery) {
        this.enableStateQuery = enableStateQuery;
    }

    public boolean equals(Object o) {
        if (o == this) {
            return true;
        }
        if (!(o instanceof QueryInfo)) {
            return false;
        }
        QueryInfo other = (QueryInfo)o;
        if (!other.canEqual((Object)this)) {
            return false;
        }
        String this$loginId = this.getLoginId();
        String other$loginId = other.getLoginId();
        if (this$loginId == null ? other$loginId != null : !this$loginId.equals(other$loginId)) {
            return false;
        }
        Date this$travelDateStart = this.getTravelDateStart();
        Date other$travelDateStart = other.getTravelDateStart();
        if (this$travelDateStart == null ? other$travelDateStart != null : !((Object)this$travelDateStart).equals(other$travelDateStart)) {
            return false;
        }
        Date this$travelDateEnd = this.getTravelDateEnd();
        Date other$travelDateEnd = other.getTravelDateEnd();
        if (this$travelDateEnd == null ? other$travelDateEnd != null : !((Object)this$travelDateEnd).equals(other$travelDateEnd)) {
            return false;
        }
        Date this$boughtDateStart = this.getBoughtDateStart();
        Date other$boughtDateStart = other.getBoughtDateStart();
        if (this$boughtDateStart == null ? other$boughtDateStart != null : !((Object)this$boughtDateStart).equals(other$boughtDateStart)) {
            return false;
        }
        Date this$boughtDateEnd = this.getBoughtDateEnd();
        Date other$boughtDateEnd = other.getBoughtDateEnd();
        if (this$boughtDateEnd == null ? other$boughtDateEnd != null : !((Object)this$boughtDateEnd).equals(other$boughtDateEnd)) {
            return false;
        }
        if (this.getState() != other.getState()) {
            return false;
        }
        if (this.isEnableTravelDateQuery() != other.isEnableTravelDateQuery()) {
            return false;
        }
        if (this.isEnableBoughtDateQuery() != other.isEnableBoughtDateQuery()) {
            return false;
        }
        return this.isEnableStateQuery() == other.isEnableStateQuery();
    }

    protected boolean canEqual(Object other) {
        return other instanceof QueryInfo;
    }

    public int hashCode() {
        int PRIME = 59;
        int result = 1;
        String $loginId = this.getLoginId();
        result = result * 59 + ($loginId == null ? 43 : $loginId.hashCode());
        Date $travelDateStart = this.getTravelDateStart();
        result = result * 59 + ($travelDateStart == null ? 43 : ((Object)$travelDateStart).hashCode());
        Date $travelDateEnd = this.getTravelDateEnd();
        result = result * 59 + ($travelDateEnd == null ? 43 : ((Object)$travelDateEnd).hashCode());
        Date $boughtDateStart = this.getBoughtDateStart();
        result = result * 59 + ($boughtDateStart == null ? 43 : ((Object)$boughtDateStart).hashCode());
        Date $boughtDateEnd = this.getBoughtDateEnd();
        result = result * 59 + ($boughtDateEnd == null ? 43 : ((Object)$boughtDateEnd).hashCode());
        result = result * 59 + this.getState();
        result = result * 59 + (this.isEnableTravelDateQuery() ? 79 : 97);
        result = result * 59 + (this.isEnableBoughtDateQuery() ? 79 : 97);
        result = result * 59 + (this.isEnableStateQuery() ? 79 : 97);
        return result;
    }

    public String toString() {
        return "QueryInfo(loginId=" + this.getLoginId() + ", travelDateStart=" + this.getTravelDateStart() + ", travelDateEnd=" + this.getTravelDateEnd() + ", boughtDateStart=" + this.getBoughtDateStart() + ", boughtDateEnd=" + this.getBoughtDateEnd() + ", state=" + this.getState() + ", enableTravelDateQuery=" + this.isEnableTravelDateQuery() + ", enableBoughtDateQuery=" + this.isEnableBoughtDateQuery() + ", enableStateQuery=" + this.isEnableStateQuery() + ")";
    }
}

