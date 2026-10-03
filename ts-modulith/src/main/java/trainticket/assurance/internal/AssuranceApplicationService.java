package trainticket.assurance.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import trainticket.assurance.AssuranceOperations;
import trainticket.assurance.AssuranceRecord;
import trainticket.assurance.AssuranceResult;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@Service
@ConditionalOnProperty(name="modulith.assurance.enabled", havingValue="true")
class AssuranceApplicationService implements AssuranceOperations {
    private final AssuranceRepository repository;
    AssuranceApplicationService(AssuranceRepository repository) { this.repository = repository; }

    private AssuranceResult<?> result(int status, String msg, Object data) { return new AssuranceResult<>(status, msg, data); }
    private Object plain(AssuranceRecord record) { return Map.of("id",record.id(),"orderId",record.orderId(),
            "typeIndex",1,"typeName","Traffic Accident Assurance","typePrice",3.0); }
    public AssuranceResult<?> all() {
        List<AssuranceRecord> records = repository.all();
        return records.isEmpty() ? result(0,"No Content, Assurance is empty",null)
                : result(1,"Success",records.stream().map(this::plain).toList());
    }
    public AssuranceResult<?> types() { return result(1,"Find All Assurance",
            List.of(Map.of("index",1,"name","Traffic Accident Assurance","price",3.0))); }
    public AssuranceResult<?> byId(UUID id) {
        AssuranceRecord record = repository.byId(id);
        return record == null ? result(0,"No Content by this id",null) : result(1,"Find Assurance Success",record);
    }
    public AssuranceResult<?> byOrder(UUID orderId) {
        AssuranceRecord record = repository.byOrder(orderId);
        return record == null ? result(0,"No Content by this orderId",null) : result(1,"Find Assurance Success",record);
    }
    public AssuranceResult<?> create(int type, UUID orderId) {
        if (repository.byOrder(orderId) != null) return result(0,"Fail.Assurance already exists",null);
        if (type != 1) return result(0,"Fail.Assurance type doesn't exist",null);
        AssuranceRecord record = new AssuranceRecord(UUID.randomUUID(),orderId,"TRAFFIC_ACCIDENT");
        repository.save(record);
        return result(1,"Success",record);
    }
    public AssuranceResult<?> modify(UUID id, UUID orderId, int type) {
        AssuranceRecord record = repository.byId(id);
        if (record == null) return result(0,"Fail.Assurance not found.",null);
        if (type != 1) return result(0,"Assurance Type not exist",null);
        // The deployed service ignores the supplied orderId and retains the existing association.
        repository.save(new AssuranceRecord(record.id(),record.orderId(),"TRAFFIC_ACCIDENT"));
        return result(1,"Modify Success",repository.byId(id));
    }
    public AssuranceResult<?> deleteById(UUID id) {
        repository.deleteById(id);
        return repository.byId(id)==null ? result(1,"Delete Success with Assurance id",null)
                : result(0,"Fail.Assurance not clear",id);
    }
    public AssuranceResult<?> deleteByOrder(UUID orderId) {
        repository.deleteByOrder(orderId);
        return repository.byOrder(orderId)==null ? result(1,"Delete Success with Order Id",null)
                : result(0,"Fail.Assurance not clear",orderId);
    }
}
