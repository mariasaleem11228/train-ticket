package trainticket.assurance;

import java.util.UUID;

public interface AssuranceOperations {
    AssuranceResult<?> all();
    AssuranceResult<?> types();
    AssuranceResult<?> byId(UUID id);
    AssuranceResult<?> byOrder(UUID orderId);
    AssuranceResult<?> create(int type, UUID orderId);
    AssuranceResult<?> modify(UUID id, UUID orderId, int type);
    AssuranceResult<?> deleteById(UUID id);
    AssuranceResult<?> deleteByOrder(UUID orderId);
}
