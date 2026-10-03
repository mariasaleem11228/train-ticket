package trainticket.consign.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import trainticket.consign.*;
import trainticket.consignprice.ConsignPriceOperations;

import java.util.List;
import java.util.UUID;

@Service
@ConditionalOnProperty(name="modulith.consign.enabled",havingValue="true")
class ConsignApplicationService implements ConsignOperations {
    private final ConsignRepository repository;
    private final ConsignPriceOperations prices;
    ConsignApplicationService(ConsignRepository repository,ConsignPriceOperations prices) {
        this.repository=repository;this.prices=prices;
    }
    private double quote(ConsignRequest request) {
        Object value=prices.quote(request.weight(),request.isWithin()).data();
        return ((Number)value).doubleValue();
    }
    public ConsignResult<ConsignRecord> create(ConsignRequest request) {
        ConsignRecord record=new ConsignRecord(UUID.randomUUID(),request.orderId(),request.accountId(),
                request.handleDate(),request.targetDate(),request.from(),request.to(),request.consignee(),
                request.phone(),request.weight(),quote(request));
        repository.save(record);
        return new ConsignResult<>(1,"You have consigned successfully! The price is "+record.price(),record);
    }
    public ConsignResult<ConsignRecord> update(ConsignRequest request) {
        ConsignRecord original=request.id()==null?null:repository.byId(request.id());
        if (original==null) return create(request);
        double price=original.weight()!=request.weight()?quote(request):original.price();
        ConsignRecord updated=new ConsignRecord(original.id(),original.orderId(),request.accountId(),
                request.handleDate(),request.targetDate(),request.from(),request.to(),request.consignee(),
                request.phone(),request.weight(),price);
        repository.save(updated);
        return new ConsignResult<>(1,"Update consign success",updated);
    }
    public ConsignResult<List<ConsignRecord>> byAccount(UUID accountId) {
        List<ConsignRecord> rows=repository.byAccount(accountId);
        return rows.isEmpty()?new ConsignResult<>(0,"No Content according to accountId",null):
                new ConsignResult<>(1,"Find consign by account id success",rows);
    }
    public ConsignResult<ConsignRecord> byOrder(UUID orderId) {
        ConsignRecord row=repository.byOrder(orderId);
        return row==null?new ConsignResult<>(0,"No Content according to order id",null):
                new ConsignResult<>(1,"Find consign by order id success",row);
    }
    public ConsignResult<List<ConsignRecord>> byConsignee(String consignee) {
        List<ConsignRecord> rows=repository.byConsignee(consignee);
        return rows.isEmpty()?new ConsignResult<>(0,"No Content according to consignee",null):
                new ConsignResult<>(1,"Find consign by consignee success",rows);
    }
}
