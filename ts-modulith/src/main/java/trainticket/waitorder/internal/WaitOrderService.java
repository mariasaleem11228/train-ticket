package trainticket.waitorder.internal;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpStatus;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;
import trainticket.runtime.WriteOwnership;
import trainticket.preserve.BookingRequest;
import trainticket.preserve.BookingResult;
import trainticket.preserve.PreserveOperations;

import java.time.*;
import java.util.Date;
import java.util.List;
import java.util.UUID;
import java.nio.charset.StandardCharsets;

@Service
@ConditionalOnProperty(name="modulith.wait-order.enabled",havingValue="true")
class WaitOrderService {
    record Result(int status,String msg,Object data) { }
    private final WaitOrderRepository repository;
    private final WriteOwnership ownership;
    private final PreserveOperations preserve;
    private final boolean writesEnabled;
    private final boolean retryEnabled;
    WaitOrderService(WaitOrderRepository repository, WriteOwnership ownership,
                     PreserveOperations preserve,
                     @Value("${modulith.wait-order.writes-enabled:false}") boolean writesEnabled,
                     @Value("${modulith.wait-order.retry-enabled:false}") boolean retryEnabled) {
        this.repository=repository;this.ownership=ownership;this.preserve=preserve;
        this.writesEnabled=writesEnabled;this.retryEnabled=retryEnabled;
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
        try { UUID.fromString(request.accountId()); UUID.fromString(request.contactsId()); }
        catch (IllegalArgumentException invalid) { return new Result(0,"Invalid account or contact ID",null); }
        Authentication caller=SecurityContextHolder.getContext().getAuthentication();
        boolean admin=caller!=null && caller.getAuthorities().stream()
                .anyMatch(role->"ROLE_ADMIN".equals(role.getAuthority()));
        if (!admin && (caller==null || !request.accountId().equals(String.valueOf(caller.getDetails()))))
            throw new ResponseStatusException(HttpStatus.FORBIDDEN,"WaitOrder account does not match token");
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
    @Scheduled(fixedDelayString="${modulith.wait-order.poll-interval-ms:5000}")
    void poll() {
        if (!writesEnabled || !ownership.permits("waitorder"))return;
        repository.expire();
        if (!retryEnabled || !ownership.permits("preserve"))return;
        WaitOrderRepository.Claim claim=repository.claimDue();
        if (claim==null)return;
        WaitOrderRecord row=claim.order();
        UUID bookingId=UUID.nameUUIDFromBytes(("waitorder:"+row.id()).getBytes(StandardCharsets.UTF_8));
        BookingRequest booking=new BookingRequest(row.accountId(),row.contactsId(),row.trainNumber(),
                row.seatType(),row.travelTime(),row.from(),row.to(),0,0,
                null,null,null,0,null,null,null,0,false);
        try {
            BookingResult result=preserve.bookWaitOrder(booking,bookingId);
            if (result.status()==1)repository.complete(claim,bookingId.toString());
            else repository.retryLater(claim,result.msg()==null?"Booking declined":result.msg(),300);
        } catch (RuntimeException failure) {
            repository.retryLater(claim,failure.getClass().getSimpleName()+": "+failure.getMessage(),300);
        }
    }
}
