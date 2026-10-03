package trainticket.travelplan.internal;

import java.util.ArrayList;
import java.util.List;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import trainticket.routeplan.RoutePlanInfo;
import trainticket.routeplan.RoutePlanOperations;
import trainticket.routeplan.RoutePlanResultUnit;
import trainticket.seat.SeatOperations;
import trainticket.seat.SeatRequest;
import trainticket.station.StationOperations;
import trainticket.travelplan.*;

@Service
@ConditionalOnProperty(name="modulith.travel-plan.enabled", havingValue="true")
class TravelPlanApplicationService implements TravelPlanOperations {
    private final RoutePlanOperations routes;
    private final StationOperations stations;
    private final SeatOperations seats;
    private final trainticket.travel.TravelOperations travel;
    private final trainticket.travel2.TravelOperations travel2;

    TravelPlanApplicationService(RoutePlanOperations routes,StationOperations stations,
            SeatOperations seats,trainticket.travel.TravelOperations travel,
            trainticket.travel2.TravelOperations travel2) {
        this.routes=routes;this.stations=stations;this.seats=seats;
        this.travel=travel;this.travel2=travel2;
    }
    public TravelPlanResult<TransferResult> transfer(TransferQuery query) {
        List<Object> first=section(query.fromStationName(),query.viaStationName(),query.travelDate());
        List<Object> second=section(query.viaStationName(),query.toStationName(),query.travelDate());
        return new TravelPlanResult<>(1,"Success.",new TransferResult(first,second));
    }
    private List<Object> section(String from,String to,java.util.Date date) {
        List<Object> result=new ArrayList<>();
        var fast=travel.search(new trainticket.travel.TripQuery(from,to,date));
        var normal=travel2.search(new trainticket.travel2.TripQuery(from,to,date));
        if(fast.data() instanceof List<?> list)result.addAll(list);
        if(normal.data() instanceof List<?> list)result.addAll(list);
        return result;
    }
    public TravelPlanResult<List<AdvancedResult>> cheapest(TravelPlanQuery query) {
        return ranked(query,0);
    }
    public TravelPlanResult<List<AdvancedResult>> quickest(TravelPlanQuery query) {
        return ranked(query,1);
    }
    public TravelPlanResult<List<AdvancedResult>> minimumStations(TravelPlanQuery query) {
        return ranked(query,2);
    }
    private TravelPlanResult<List<AdvancedResult>> ranked(TravelPlanQuery query,int kind) {
        RoutePlanInfo info=new RoutePlanInfo(query.startingPlace(),query.endPlace(),query.departureTime(),5);
        List<RoutePlanResultUnit> ranked=switch(kind) {
            case 0 -> routes.cheapest(info).data();
            case 1 -> routes.quickest(info).data();
            default -> routes.minimumStops(info).data();
        };
        if(ranked==null || ranked.isEmpty())return new TravelPlanResult<>(0,"Cannot Find",null);
        List<AdvancedResult> result=new ArrayList<>();
        for(RoutePlanResultUnit unit:ranked) {
            @SuppressWarnings("unchecked")
            List<String> names=(List<String>)stations.namesForIds(unit.stopStations()).getData();
            int first=left(query,unit,2);
            int second=left(query,unit,3);
            result.add(new AdvancedResult(unit.tripId(),unit.trainTypeId(),unit.fromStationName(),
                    unit.toStationName(),names,unit.priceForSecondClassSeat(),second,
                    unit.priceForFirstClassSeat(),first,unit.startingTime(),unit.endTime()));
        }
        return new TravelPlanResult<>(1,"Success",result);
    }
    private int left(TravelPlanQuery query,RoutePlanResultUnit unit,int seatType) {
        SeatRequest request=new SeatRequest();
        request.setTravelDate(query.departureTime());
        request.setTrainNumber(unit.tripId());
        request.setStartStation((String)stations.idForName(unit.fromStationName()).getData());
        request.setDestStation((String)stations.idForName(unit.toStationName()).getData());
        request.setSeatType(seatType);
        return seats.leftTickets(request).data();
    }
}
