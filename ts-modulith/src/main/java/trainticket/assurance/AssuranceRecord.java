package trainticket.assurance;

import java.util.UUID;

public record AssuranceRecord(UUID id, UUID orderId, String type) { }
