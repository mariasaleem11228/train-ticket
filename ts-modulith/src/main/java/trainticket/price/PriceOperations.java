package trainticket.price;

import java.util.List;

/** Published Price API for later Travel and administration modules. */
public interface PriceOperations {
    PriceResult<List<PriceConfig>> all();
    PriceResult<PriceConfig> find(String routeId,String trainType);
    PriceResult<PriceConfig> create(PriceConfig config);
    PriceResult<PriceConfig> update(PriceConfig config);
    PriceResult<PriceConfig> delete(PriceConfig config);
}
