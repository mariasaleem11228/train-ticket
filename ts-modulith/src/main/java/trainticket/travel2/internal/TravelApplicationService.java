package trainticket.travel2.internal;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import trainticket.orders.OrderOperations;
import trainticket.orders.SoldTicket;
import trainticket.route.Route;
import trainticket.route.RouteOperations;
import trainticket.seat.SeatOperations;
import trainticket.seat.SeatRequest;
import trainticket.train.TrainOperations;
import trainticket.train.TrainType;
import trainticket.ticketinfo.TicketInfoOperations;
import trainticket.travel2.*;
import java.time.Duration;

/** Deployed Travel behavior. The still-remote TicketInfo service is an HTTP adapter. */
@Service("travel2ApplicationService")
@ConditionalOnProperty(name="modulith.travel2.enabled",havingValue="true")
class TravelApplicationService implements TravelOperations {
    private final TripRepository trips;
    private final TrainOperations trains;
    private final RouteOperations routes;
    private final OrderOperations orders;
    private final SeatOperations seats;
    private final RestTemplate http;
    private final String ticketInfoUrl;
    private final ObjectProvider<TicketInfoOperations> ticketInfo;
    private final ObjectMapper mapper;

    TravelApplicationService(TripRepository trips, TrainOperations trains, RouteOperations routes,
                             OrderOperations orders, SeatOperations seats,
                             @Value("${modulith.travel2.ticket-info-url:http://ts-ticketinfo-service:15681}") String ticketInfoUrl,
                             ObjectProvider<TicketInfoOperations> ticketInfo,ObjectMapper mapper) {
        this.trips=trips;this.trains=trains;this.routes=routes;this.orders=orders;this.seats=seats;
        this.ticketInfoUrl=ticketInfoUrl;
        this.ticketInfo=ticketInfo;this.mapper=mapper;
        SimpleClientHttpRequestFactory factory=new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(Duration.ofSeconds(5));
        factory.setReadTimeout(Duration.ofSeconds(20));
        this.http=new RestTemplate(factory);
    }
    public TravelResult<List<Trip>> all() {
        List<Trip> found=trips.all();
        return found.isEmpty() ? new TravelResult<>(0,"No Content",null) : new TravelResult<>(1,"Success",found);
    }
    public TravelResult<Trip> find(String tripId) {
        Trip found=trips.find(TripId.parse(tripId));
        return found==null ? new TravelResult<>(0,"No Content according to tripId"+tripId,null)
                : new TravelResult<>(1,"Search Trip Success by Trip Id "+tripId,found);
    }
    public TravelResult<?> create(TravelInfo info) {
        TripId id=TripId.parse(info.tripId());
        if(trips.find(id)!=null) return new TravelResult<>(1,"Trip "+info.tripId()+" already exists",null);
        trips.save(toTrip(info));
        return new TravelResult<>(1,"Create trip info:"+id+".",null);
    }
    public TravelResult<?> update(TravelInfo info) {
        TripId id=TripId.parse(info.tripId());
        if(trips.find(id)==null) return new TravelResult<>(1,"Trip"+info.tripId()+"doesn 't exists",null);
        Trip trip=toTrip(info);trips.save(trip);
        return new TravelResult<>(1,"Update trip info:"+id,trip);
    }
    public TravelResult<?> delete(String tripId) {
        TripId id=TripId.parse(tripId);
        if(trips.find(id)==null) return new TravelResult<>(0,"Trip "+tripId+" doesn't exist.",null);
        trips.delete(id);return new TravelResult<>(1,"Delete trip:"+tripId+".",tripId);
    }
    private Trip toTrip(TravelInfo info) {
        return new Trip(TripId.parse(info.tripId()),info.trainTypeId(),info.routeId(),info.startingTime(),
                info.startingStationId(),info.stationsId(),info.terminalStationId(),info.endTime());
    }
    public TravelResult<?> routes(List<String> routeIds) {
        if(routeIds.isEmpty())return new TravelResult<>(0,"No Content",null);
        List<List<Trip>> result=new ArrayList<>();
        for(String id:routeIds)result.add(trips.byRoute(id));
        return new TravelResult<>(1,"Success",result);
    }
    public TravelResult<?> trainType(String tripId) {
        Trip trip=trips.find(TripId.parse(tripId));
        TrainType train=trip==null ? null : trains.find(trip.trainTypeId()).data();
        return train==null ? new TravelResult<>(0,"No Content",null) : new TravelResult<>(1,"Success query Train by trip id",train);
    }
    public TravelResult<?> route(String tripId) {
        Trip trip=tripId==null || tripId.length()<2 ? null : trips.find(TripId.parse(tripId));
        Route route=trip==null ? null : routes.find(trip.routeId()).data();
        return route==null ? new TravelResult<>(0,"\"[Get Route By Trip ID] Trip Not Found:\" + tripId",null)
                : new TravelResult<>(1,"[Get Route By Trip ID] Success",route);
    }
    public TravelResult<?> adminAll() {
        List<Map<String,Object>> result=new ArrayList<>();
        for(Trip trip:trips.all()) {
            Map<String,Object> item=new LinkedHashMap<>();
            item.put("trip",trip);item.put("trainType",trains.find(trip.trainTypeId()).data());
            item.put("route",routes.find(trip.routeId()).data());result.add(item);
        }
        return result.isEmpty() ? new TravelResult<>(0,"No Content",null) : new TravelResult<>(1,"Travel Service Admin Query All Travel Success",result);
    }
    public TravelResult<?> search(TripQuery query) {
        String startId=stationId(query.startingPlace());
        String endId=stationId(query.endPlace());
        List<TripResponse> result=new ArrayList<>();
        for(Trip trip:trips.all()) {
            Route route=routes.find(trip.routeId()).data();
            if(route==null)continue;
            List<String> stops=route.getStations();
            if(stops.contains(startId) && stops.contains(endId) && stops.indexOf(startId)<stops.indexOf(endId)) {
                TripResponse response=tickets(trip,route,startId,endId,query.startingPlace(),query.endPlace(),query.departureTime());
                if(response==null)return new TravelResult<>(0,"No Content",null);
                result.add(response);
            }
        }
        return new TravelResult<>(1,"Success Query",result);
    }
    public TravelResult<?> detail(TripDetailQuery query) {
        Map<String,Object> detail=new LinkedHashMap<>();
        Trip trip=trips.find(TripId.parse(query.tripId()));
        TripResponse response=null;
        if(trip!=null) {
            String startId=stationId(query.from());String endId=stationId(query.to());
            Route route=routes.find(trip.routeId()).data();
            response=tickets(trip,route,startId,endId,query.from(),query.to(),query.travelDate());
        }
        detail.put("status",false);detail.put("message",null);
        detail.put("tripResponse",response);detail.put("trip",response==null ? null : trip);
        return new TravelResult<>(1,"Success",detail);
    }
    private String stationId(String name) {
        TicketInfoOperations local=ticketInfo.getIfAvailable();
        JsonNode response=local==null?http.getForObject(ticketInfoUrl+"/api/v1/ticketinfoservice/ticketinfo/"+name,JsonNode.class):
                mapper.valueToTree(local.stationId(name));
        JsonNode data=response==null ? null : response.path("data");
        return data==null || data.isNull() || data.isMissingNode() ? null : data.asText();
    }
    private TripResponse tickets(Trip trip,Route route,String startId,String endId,
                                 String startName,String endName,Date date) {
        if(!afterToday(date))return null;
        Map<String,Object> ticketRequest=new LinkedHashMap<>();
        ticketRequest.put("trip",trip);ticketRequest.put("startingPlace",startName);
        ticketRequest.put("endPlace",endName);ticketRequest.put("departureTime",date);
        TicketInfoOperations local=ticketInfo.getIfAvailable();
        JsonNode info=local==null?http.postForObject(ticketInfoUrl+"/api/v1/ticketinfoservice/ticketinfo",ticketRequest,JsonNode.class):
                mapper.valueToTree(local.travel(mapper.valueToTree(ticketRequest)));
        JsonNode fares=info.path("data").path("prices");
        SoldTicket sold=(SoldTicket)orders.queryAlreadySoldOrders(date,trip.tripId().toString()).getData();
        String number=sold.getTrainNumber();
        int first=left(date,number,startName,endName,2);
        int second=left(date,number,startName,endName,3);
        int from=route.getStations().indexOf(startId),to=route.getStations().indexOf(endId);
        int fromDistance=route.getDistances().get(from)-route.getDistances().get(0);
        int toDistance=route.getDistances().get(to)-route.getDistances().get(0);
        TrainType train=trains.find(trip.trainTypeId()).data();
        int fromMinutes=60*fromDistance/train.getAverageSpeed();
        int toMinutes=60*toDistance/train.getAverageSpeed();
        Calendar start=Calendar.getInstance();start.setTime(trip.startingTime());start.add(Calendar.MINUTE,fromMinutes);
        Calendar end=Calendar.getInstance();end.setTime(trip.startingTime());end.add(Calendar.MINUTE,toMinutes);
        return new TripResponse(trip.tripId(),trip.trainTypeId(),startName,endName,start.getTime(),end.getTime(),
                second,first,fares.path("economyClass").asText(),fares.path("confortClass").asText());
    }
    private int left(Date date,String number,String start,String end,int seatType) {
        SeatRequest request=new SeatRequest();request.setTravelDate(date);request.setTrainNumber(number);
        request.setStartStation(stationId(start));request.setDestStation(stationId(end));request.setSeatType(seatType);
        return seats.leftTickets(request).data();
    }
    private boolean afterToday(Date date) {
        return date!=null && !LocalDate.ofInstant(date.toInstant(),ZoneId.systemDefault()).isBefore(LocalDate.now());
    }
}
