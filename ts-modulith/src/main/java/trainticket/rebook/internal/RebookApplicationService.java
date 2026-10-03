package trainticket.rebook.internal;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;
import trainticket.insidepayment.InsidePaymentOperations;
import trainticket.insidepayment.InsidePaymentRequest;
import trainticket.orderother.OrderOtherOperations;
import trainticket.orders.Order;
import trainticket.orders.OrderOperations;
import trainticket.rebook.RebookInfo;
import trainticket.rebook.RebookOperations;
import trainticket.rebook.RebookResult;
import trainticket.runtime.WriteOwnership;
import trainticket.seat.SeatOperations;
import trainticket.seat.SeatRequest;
import trainticket.seat.SeatResult;
import trainticket.seat.SeatTicket;
import trainticket.station.StationOperations;
import trainticket.travel.TripDetailQuery;
import java.math.BigDecimal;
import java.util.Calendar;
import java.util.Date;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;

/** Deployed Rebook workflow using published local module APIs. */
@Service
@ConditionalOnProperty(name="modulith.rebook.enabled",havingValue="true")
class RebookApplicationService implements RebookOperations {
    private final OrderOperations orders;
    private final OrderOtherOperations otherOrders;
    private final StationOperations stations;
    private final trainticket.travel.TravelOperations travel;
    private final trainticket.travel2.TravelOperations travel2;
    private final SeatOperations seats;
    private final InsidePaymentOperations wallet;
    private final WriteOwnership ownership;
    private final ObjectMapper mapper;
    private final boolean writesEnabled;

    RebookApplicationService(OrderOperations orders,OrderOtherOperations otherOrders,
            StationOperations stations,trainticket.travel.TravelOperations travel,
            trainticket.travel2.TravelOperations travel2,SeatOperations seats,
            InsidePaymentOperations wallet,WriteOwnership ownership,ObjectMapper mapper,
            @Value("${modulith.rebook.writes-enabled:false}") boolean writesEnabled) {
        this.orders=orders;this.otherOrders=otherOrders;this.stations=stations;
        this.travel=travel;this.travel2=travel2;this.seats=seats;this.wallet=wallet;
        this.ownership=ownership;this.mapper=mapper;this.writesEnabled=writesEnabled;
    }

    @Override public RebookResult<?> rebook(RebookInfo info) {
        requireWriter();
        Order order=find(info);
        if(order==null)return fail("order not found");
        if(order.getStatus()!=1)return fail("you order not suitable to rebook!");
        if(!checkTime(order.getTravelDate(),order.getTravelTime()))
            return fail("You can only change the ticket before the train start or within 2 hours after the train start.");
        Journey journey=detail(order,info);
        if(journey.status()==0)return fail(journey.message());
        if(journey.response()==null||journey.trip()==null)return fail("No Trip info content");
        if(noSeat(journey,info.getSeatType()))return fail("Seat Not Enough");
        String newPrice=price(journey,info.getSeatType());
        BigDecimal delta=new BigDecimal(order.getPrice()).subtract(new BigDecimal(newPrice));
        if(delta.signum()>0) {
            if(wallet.drawBack(info.getLoginId(),delta.toString()).status()!=1)
                return fail("Can't draw back the difference money, please try again!");
            return update(order,info,journey,newPrice);
        }
        if(delta.signum()==0)return update(order,info,journey,newPrice);
        return new RebookResult<>(2,"Please pay the different money!",
                                  differenceQuote(delta.negate().toString()));
    }

    @Override public RebookResult<?> payDifference(RebookInfo info) {
        requireWriter();
        Order order=find(info);
        if(order==null)return fail("order not found");
        Journey journey=detail(order,info);
        if(journey.response()==null||journey.trip()==null)return fail("No Trip info content");
        String newPrice=price(journey,info.getSeatType());
        String difference=new BigDecimal(newPrice).subtract(new BigDecimal(order.getPrice())).toString();
        if(wallet.payDifference(new InsidePaymentRequest(info.getLoginId(),info.getOrderId(),
                info.getTripId(),difference)).status()==1)
            return update(order,info,journey,newPrice);
        return fail("Can't pay the difference,please try again");
    }

    private Order find(RebookInfo info) {
        if(standard(info.getOldTripId())) {
            var found=orders.getOrderById(info.getOrderId());
            return found.getStatus()==1?(Order)found.getData():null;
        }
        var found=otherOrders.getOrderById(info.getOrderId());
        return found.getStatus()==1?mapper.convertValue(found.getData(),Order.class):null;
    }
    private Journey detail(Order order,RebookInfo info) {
        String from=(String)stations.nameForId(order.getFrom()).getData();
        String to=(String)stations.nameForId(order.getTo()).getData();
        if(standard(info.getTripId())) {
            var found=travel.detail(new TripDetailQuery(info.getTripId(),info.getDate(),from,to));
            Map<?,?> data=(Map<?,?>)found.data();
            return new Journey(found.status(),found.msg(),
                    data==null?null:data.get("tripResponse"),data==null?null:data.get("trip"));
        }
        var found=travel2.detail(new trainticket.travel2.TripDetailQuery(
                info.getTripId(),info.getDate(),from,to));
        Map<?,?> data=(Map<?,?>)found.data();
        return new Journey(found.status(),found.msg(),
                data==null?null:data.get("tripResponse"),data==null?null:data.get("trip"));
    }
    private boolean noSeat(Journey journey,int seatType) {
        int first=journey.first(),second=journey.second();
        return seatType==2?first<=0:second==3&&first<=0;
    }
    private String price(Journey journey,int seatType) {
        if(seatType==2)return journey.firstPrice();
        if(seatType==3)return journey.secondPrice();
        return "0";
    }
    private RebookResult<?> update(Order order,RebookInfo info,Journey journey,String newPrice) {
        String oldTrip=order.getTrainNumber();
        String oldId=Objects.toString(order.getId());
        order.setTrainNumber(info.getTripId());order.setBoughtDate(new Date());
        order.setStatus(3);order.setPrice(newPrice);order.setSeatClass(info.getSeatType());
        order.setTravelDate(info.getDate());order.setTravelTime(journey.startTime());
        SeatRequest request=new SeatRequest();request.setTravelDate(info.getDate());
        request.setTrainNumber(info.getTripId());request.setStartStation(order.getFrom());
        request.setDestStation(order.getTo());request.setSeatType(info.getSeatType()==2?2:3);
        SeatResult<SeatTicket> seat=seats.distribute(request);
        if(seat.status()!=1||seat.data()==null)return fail("Seat Not Enough");
        order.setSeatClass(info.getSeatType()==2?2:3);
        order.setSeatNumber(Integer.toString(seat.data().seatNo()));
        if(standard(oldTrip)==standard(info.getTripId())) {
            int status=standard(info.getTripId())?orders.updateOrder(order).getStatus():
                    otherOrders.updateOrder(mapper.convertValue(order,trainticket.orderother.Order.class)).getStatus();
            return status==1?new RebookResult<>(1,"Success!",order):fail("Can't update Order!");
        }
        // Create first. The deployed service deletes the only order before creating
        // its replacement and leaves it lost if creation fails.
        String newId;
        if(standard(info.getTripId())) {
            var created=orders.addNewOrder(order);
            if(created.getStatus()!=1)return fail("Can't update Order!");
            newId=((Order)created.getData()).getId().toString();
            order.setId(java.util.UUID.fromString(oldId));
        } else {
            var created=otherOrders.addNewOrder(
                    mapper.convertValue(order,trainticket.orderother.Order.class));
            if(created.getStatus()!=1)return fail("Can't update Order!");
            newId=((trainticket.orderother.Order)created.getData()).getId().toString();
        }
        int removed=standard(oldTrip)?orders.deleteOrder(oldId).getStatus():
                otherOrders.deleteOrder(oldId).getStatus();
        if(removed!=1) {
            if(standard(info.getTripId()))orders.deleteOrder(newId);
            else otherOrders.deleteOrder(newId);
            return fail("Can't update Order!");
        }
        return new RebookResult<>(1,"Success",order);
    }
    private Map<String,Object> differenceQuote(String difference) {
        Map<String,Object> quote=new LinkedHashMap<>();
        quote.put("id",null);quote.put("boughtDate",new Date());
        quote.put("travelDate",new Date(123456789L));quote.put("travelTime",null);
        quote.put("accountId",null);quote.put("contactsName",null);
        quote.put("documentType",0);quote.put("contactsDocumentNumber",null);
        quote.put("trainNumber","G1235");quote.put("coachNumber",5);
        quote.put("seatClass",2);quote.put("seatNumber","5A");
        quote.put("from","shanghai");quote.put("to","taiyuan");
        quote.put("status",1);quote.put("price","0.0");
        quote.put("differenceMoney",difference);
        return quote;
    }
    private boolean standard(String trip){return trip.startsWith("G")||trip.startsWith("D");}
    private boolean checkTime(Date date,Date time) {
        Calendar now=Calendar.getInstance(),travelDate=Calendar.getInstance(),travelTime=Calendar.getInstance();
        travelDate.setTime(date);travelTime.setTime(time);
        int year=now.get(Calendar.YEAR)-travelDate.get(Calendar.YEAR);
        if(year!=0)return year<0;
        int month=now.get(Calendar.MONTH)-travelDate.get(Calendar.MONTH);
        if(month!=0)return month<0;
        int day=now.get(Calendar.DAY_OF_MONTH)-travelDate.get(Calendar.DAY_OF_MONTH);
        if(day!=0)return day<0;
        int hour=now.get(Calendar.HOUR_OF_DAY)-travelTime.get(Calendar.HOUR_OF_DAY)-2;
        return hour<0||hour==0&&now.get(Calendar.MINUTE)<=travelTime.get(Calendar.MINUTE);
    }
    private void requireWriter() {
        if(!writesEnabled||!ownership.permits("rebook"))
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,"Rebook writes disabled");
    }
    private RebookResult<?> fail(String message){return new RebookResult<>(0,message,null);}
    private record Journey(int status,String message,Object response,Object trip) {
        int first(){return response instanceof trainticket.travel.TripResponse r?r.confortClass():
                ((trainticket.travel2.TripResponse)response).confortClass();}
        int second(){return response instanceof trainticket.travel.TripResponse r?r.economyClass():
                ((trainticket.travel2.TripResponse)response).economyClass();}
        String firstPrice(){return response instanceof trainticket.travel.TripResponse r?r.priceForConfortClass():
                ((trainticket.travel2.TripResponse)response).priceForConfortClass();}
        String secondPrice(){return response instanceof trainticket.travel.TripResponse r?r.priceForEconomyClass():
                ((trainticket.travel2.TripResponse)response).priceForEconomyClass();}
        Date startTime(){return trip instanceof trainticket.travel.Trip r?r.startingTime():
                ((trainticket.travel2.Trip)trip).startingTime();}
    }
}
