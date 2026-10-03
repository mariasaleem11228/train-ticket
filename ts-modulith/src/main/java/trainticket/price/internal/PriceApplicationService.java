package trainticket.price.internal;

import java.util.List;
import java.util.UUID;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import trainticket.price.PriceConfig;
import trainticket.price.PriceOperations;
import trainticket.price.PriceResult;

@Service
@ConditionalOnProperty(name="modulith.price.enabled",havingValue="true")
class PriceApplicationService implements PriceOperations {
    private final PriceRepository repository;
    PriceApplicationService(PriceRepository repository) { this.repository=repository; }
    public PriceResult<List<PriceConfig>> all() {
        List<PriceConfig> result=repository.all();
        return result.isEmpty() ? new PriceResult<>(0,"No price config",null)
                : new PriceResult<>(1,"Success",result);
    }
    public PriceResult<PriceConfig> find(String routeId,String trainType) {
        PriceConfig found=repository.find(routeId,trainType);
        return found==null ? new PriceResult<>(0,"No that config",null)
                : new PriceResult<>(1,"Success",found);
    }
    public PriceResult<PriceConfig> create(PriceConfig input) {
        PriceConfig config=new PriceConfig(input.getId()==null ? UUID.randomUUID() : input.getId(),
                input.getTrainType(),input.getRouteId(),input.getBasicPriceRate(),input.getFirstClassPriceRate());
        repository.save(config);
        return new PriceResult<>(1,"Create success",config);
    }
    public PriceResult<PriceConfig> update(PriceConfig input) {
        if (repository.find(input.getId())==null) return new PriceResult<>(0,"No that config",null);
        PriceConfig config=new PriceConfig(input.getId(),input.getTrainType(),input.getRouteId(),
                input.getBasicPriceRate(),input.getFirstClassPriceRate());
        repository.save(config);
        return new PriceResult<>(1,"Update success",config);
    }
    public PriceResult<PriceConfig> delete(PriceConfig input) {
        if (repository.find(input.getId())==null) return new PriceResult<>(0,"No that config",null);
        repository.delete(input.getId());
        return new PriceResult<>(1,"Delete success",input);
    }
}
