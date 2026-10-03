package trainticket.consign;

import java.util.UUID;

public record ConsignRecord(UUID id, UUID orderId, UUID accountId, String handleDate,
                            String targetDate, String from, String to, String consignee,
                            String phone, double weight, double price) { }
