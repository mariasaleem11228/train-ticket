package trainticket.waitorder.internal;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpStatus;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;
import trainticket.runtime.WriteOwnership;

import java.time.*;
import java.util.Date;
import java.util.List;
import java.util.UUID;

@Service
@ConditionalOnProperty(name="modulith.wait-order.enabled",havingValue="true")
class WaitOrderService {
    record Result(int status,String msg,Object data) { }
    private final WaitOrderRepository repository;
    private final WriteOwnership ownership;
    private final boolean writesEnabled;
    WaitOrderService(WaitOrderRepository repository, WriteOwnership ownership,
                     @Value("${modulith.wait-order.writes-enabled:false}") boolean writesEnabled) {
        this.repository=repository;this.ownership=ownership;this.writesEnabled=writesEnabled;
    }
    private void requireWrite() {
        if (!writesEnabled || !ownership.permits("waitorder"))
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,"WaitOrder writes disabled");
    }
    Result create(WaitOrderRequest request) {
        requireWrite();
        if (request.accountId()==null || request.accountId().isBlank() || request.contactsId()==null
                || request.contactsId().isBlank() || request.tripId()==null || request.tripId().isBlank()
                || request.date()==null || request.from()==null || request.to()==null)
            return new Result(0,"Invalid wait order",null);
        final LocalDate travel;
        try { travel=LocalDate.parse(request.date()); }
        catch (RuntimeException invalid) { return new Result(0,"Invalid travel date",null); }
        Date now=new Date();
        Date travelTime=Date.from(travel.atStartOfDay(ZoneId.systemDefault()).toInstant());
        WaitOrderRecord order=new WaitOrderRecord(UUID.randomUUID().toString(),travelTime,
                request.accountId(),request.contactsId(),null,0,null,request.tripId(),request.seatType(),
                request.from(),request.to(),request.price(),Date.from(Instant.now().plus(Duration.ofDays(1))),now,0);
        return repository.createIfAbsent(order)?new Result(1,"Success",null):
                new Result(0,"Order already exist",null);
    }
    Result list(boolean waiting) {
        List<WaitOrderRecord> all=repository.all();
        if (all.isEmpty())return new Result(0,"No Content.",null);
        return new Result(1,"Success.",waiting?all.stream().filter(row->row.status()==0 || row.status()==1).toList():all);
    }
    @Scheduled(fixedDelayString="${modulith.wait-order.expiry-interval-ms:300000}")
    void expire() { if (writesEnabled && ownership.permits("waitorder"))repository.expire(); }
}
