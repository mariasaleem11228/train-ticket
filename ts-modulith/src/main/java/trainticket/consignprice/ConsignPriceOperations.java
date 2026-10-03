package trainticket.consignprice;

public interface ConsignPriceOperations {
    ConsignPriceResult<?> config();
    ConsignPriceResult<?> description();
    ConsignPriceResult<?> quote(double weight, boolean withinRegion);
    ConsignPriceResult<?> update(ConsignPrice config);
}
