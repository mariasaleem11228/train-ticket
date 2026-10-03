package trainticket.travelplan;

import java.util.List;

public interface TravelPlanOperations {
    TravelPlanResult<TransferResult> transfer(TransferQuery query);
    TravelPlanResult<List<AdvancedResult>> cheapest(TravelPlanQuery query);
    TravelPlanResult<List<AdvancedResult>> quickest(TravelPlanQuery query);
    TravelPlanResult<List<AdvancedResult>> minimumStations(TravelPlanQuery query);
}
