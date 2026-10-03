package trainticket.routeplan.internal;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import trainticket.route.Route;
import trainticket.route.RouteOperations;
import trainticket.routeplan.*;
import trainticket.station.StationOperations;

@Service
@ConditionalOnProperty(name="modulith.route-plan.enabled", havingValue="true")
class RoutePlanApplicationService implements RoutePlanOperations {
    private final StationOperations stations;
    private final RouteOperations routes;
    private final trainticket.travel.TravelOperations travel;
    private final trainticket.travel2.TravelOperations travel2;

    RoutePlanApplicationService(StationOperations stations, RouteOperations routes,
            trainticket.travel.TravelOperations travel,
            trainticket.travel2.TravelOperations travel2) {
        this.stations=stations; this.routes=routes; this.travel=travel; this.travel2=travel2;
    }

    public RoutePlanResult<List<RoutePlanResultUnit>> cheapest(RoutePlanInfo info) {
        List<Journey> journeys=journeys(info);
        journeys.sort(Comparator.comparingDouble(j -> Double.parseDouble(j.priceForEconomyClass())));
        return new RoutePlanResult<>(1,"Success",units(journeys,5));
    }
    public RoutePlanResult<List<RoutePlanResultUnit>> quickest(RoutePlanInfo info) {
        List<Journey> journeys=journeys(info);
        journeys.sort(Comparator.comparingLong(j -> j.endTime().getTime()-j.startingTime().getTime()));
        return new RoutePlanResult<>(1,"Success",units(journeys,5));
    }
    public RoutePlanResult<List<RoutePlanResultUnit>> minimumStops(RoutePlanInfo info) {
        String from=(String)stations.idForName(info.formStationName()).getData();
        String to=(String)stations.idForName(info.toStationName()).getData();
        List<Route> candidates=new ArrayList<>(routes.between(from,to).data());
        candidates.sort(Comparator.comparingInt(r -> r.getStations().indexOf(to)-r.getStations().indexOf(from)));
        List<Route> selected=candidates.subList(0,Math.min(5,candidates.size()));
        List<String> routeIds=selected.stream().map(Route::getId).toList();
        List<Journey> journeys=new ArrayList<>();
        appendTrips(journeys,travel2.routes(routeIds).data(),info,false);
        appendTrips(journeys,travel.routes(routeIds).data(),info,true);
        return new RoutePlanResult<>(1,"Success.",units(journeys,journeys.size()));
    }
    private List<Journey> journeys(RoutePlanInfo info) {
        List<Journey> result=new ArrayList<>();
        var fast=travel.search(new trainticket.travel.TripQuery(info.formStationName(),info.toStationName(),info.travelDate()));
        var other=travel2.search(new trainticket.travel2.TripQuery(info.formStationName(),info.toStationName(),info.travelDate()));
        appendResponses(result,fast.data());appendResponses(result,other.data());
        return result;
    }
    private void appendResponses(List<Journey> target,Object data) {
        if(data instanceof List<?> list)
            for(Object item:list) {
                if(item instanceof trainticket.travel.TripResponse r)
                    target.add(new Journey(r.tripId().toString(),r.trainTypeId(),r.startingStation(),r.terminalStation(),
                            r.startingTime(),r.endTime(),r.priceForEconomyClass(),r.priceForConfortClass()));
                else if(item instanceof trainticket.travel2.TripResponse r)
                    target.add(new Journey(r.tripId().toString(),r.trainTypeId(),r.startingStation(),r.terminalStation(),
                            r.startingTime(),r.endTime(),r.priceForEconomyClass(),r.priceForConfortClass()));
            }
    }
    private void appendTrips(List<Journey> target,Object data,RoutePlanInfo info,boolean fast) {
        if(!(data instanceof List<?> groups))return;
        for(Object group:groups)if(group instanceof List<?> trips)for(Object trip:trips) {
            String id;
            if(trip instanceof trainticket.travel.Trip t)id=t.tripId().toString();
            else if(trip instanceof trainticket.travel2.Trip t)id=t.tripId().toString();
            else continue;
            Object result=fast
                    ?travel.detail(new trainticket.travel.TripDetailQuery(id,info.travelDate(),info.formStationName(),info.toStationName())).data()
                    :travel2.detail(new trainticket.travel2.TripDetailQuery(id,info.travelDate(),info.formStationName(),info.toStationName())).data();
            if(result instanceof Map<?,?> map)appendResponses(target,List.of(map.get("tripResponse")));
        }
    }
    private List<RoutePlanResultUnit> units(List<Journey> journeys,int limit) {
        List<RoutePlanResultUnit> result=new ArrayList<>();
        for(Journey journey:journeys.subList(0,Math.min(limit,journeys.size()))) {
            Object route=journey.tripId().charAt(0)=='G'||journey.tripId().charAt(0)=='D'
                    ? travel.route(journey.tripId()).data() : travel2.route(journey.tripId()).data();
            List<String> stops=((Route)route).getStations();
            result.add(new RoutePlanResultUnit(journey.tripId(),journey.trainTypeId(),journey.from(),journey.to(),
                    stops,journey.priceForEconomyClass(),journey.priceForConfortClass(),
                    journey.startingTime(),journey.endTime()));
        }
        return result;
    }
    private record Journey(String tripId,String trainTypeId,String from,String to,
            java.util.Date startingTime,java.util.Date endTime,
            String priceForEconomyClass,String priceForConfortClass) { }
}
