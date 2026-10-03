package trainticket.routeplan;

import java.util.Date;

public record RoutePlanInfo(String formStationName, String toStationName,
                            Date travelDate, int num) { }
