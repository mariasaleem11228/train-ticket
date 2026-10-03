package trainticket.consignprice.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import trainticket.consignprice.ConsignPrice;
import trainticket.consignprice.ConsignPriceOperations;
import trainticket.consignprice.ConsignPriceResult;

@Service
@ConditionalOnProperty(name="modulith.consign-price.enabled",havingValue="true")
class ConsignPriceApplicationService implements ConsignPriceOperations {
    private final ConsignPriceRepository repository;
    ConsignPriceApplicationService(ConsignPriceRepository repository) { this.repository=repository; }
    private ConsignPriceResult<?> result(Object data) { return new ConsignPriceResult<>(1,"Success",data); }
    public ConsignPriceResult<?> config() { return result(repository.current()); }
    public ConsignPriceResult<?> description() {
        ConsignPrice price=repository.current();
        return result("The price of weight within "+price.initialWeight()+" is "+price.initialPrice()+
                ". The price of extra weight within the region is "+price.withinPrice()+
                " and beyond the region is "+price.beyondPrice()+"\n");
    }
    public ConsignPriceResult<?> quote(double weight,boolean withinRegion) {
        ConsignPrice price=repository.current();
        double amount=weight<=price.initialWeight() ? price.initialPrice() : price.initialPrice()+
                (weight-price.initialWeight())*(withinRegion?price.withinPrice():price.beyondPrice());
        return result(amount);
    }
    public ConsignPriceResult<?> update(ConsignPrice input) {
        ConsignPrice updated=new ConsignPrice(input.id(),0,input.initialWeight(),input.initialPrice(),
                input.withinPrice(),input.beyondPrice());
        repository.save(updated);
        return result(updated);
    }
}
