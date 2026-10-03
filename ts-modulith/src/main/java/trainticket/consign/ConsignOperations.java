package trainticket.consign;

import java.util.List;
import java.util.UUID;

public interface ConsignOperations {
    ConsignResult<ConsignRecord> create(ConsignRequest request);
    ConsignResult<ConsignRecord> update(ConsignRequest request);
    ConsignResult<List<ConsignRecord>> byAccount(UUID accountId);
    ConsignResult<ConsignRecord> byOrder(UUID orderId);
    ConsignResult<List<ConsignRecord>> byConsignee(String consignee);
}
