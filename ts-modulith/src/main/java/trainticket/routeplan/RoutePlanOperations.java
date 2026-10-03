package trainticket.routeplan;

import java.util.List;

public interface RoutePlanOperations {
    RoutePlanResult<List<RoutePlanResultUnit>> cheapest(RoutePlanInfo info);
    RoutePlanResult<List<RoutePlanResultUnit>> quickest(RoutePlanInfo info);
    RoutePlanResult<List<RoutePlanResultUnit>> minimumStops(RoutePlanInfo info);
}
