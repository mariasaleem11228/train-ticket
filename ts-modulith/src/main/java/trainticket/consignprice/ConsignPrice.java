package trainticket.consignprice;

import java.util.UUID;

public record ConsignPrice(UUID id, int index, double initialWeight, double initialPrice,
                           double withinPrice, double beyondPrice) { }
