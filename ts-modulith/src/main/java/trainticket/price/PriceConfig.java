package trainticket.price;

import java.util.UUID;

/** Deployed Price JSON contract. */
public class PriceConfig {
    private UUID id;
    private String trainType;
    private String routeId;
    private double basicPriceRate;
    private double firstClassPriceRate;
    public PriceConfig() { }
    public PriceConfig(UUID id,String trainType,String routeId,double basicPriceRate,double firstClassPriceRate) {
        this.id=id;this.trainType=trainType;this.routeId=routeId;
        this.basicPriceRate=basicPriceRate;this.firstClassPriceRate=firstClassPriceRate;
    }
    public UUID getId() { return id; }
    public void setId(UUID id) { this.id=id; }
    public String getTrainType() { return trainType; }
    public void setTrainType(String trainType) { this.trainType=trainType; }
    public String getRouteId() { return routeId; }
    public void setRouteId(String routeId) { this.routeId=routeId; }
    public double getBasicPriceRate() { return basicPriceRate; }
    public void setBasicPriceRate(double basicPriceRate) { this.basicPriceRate=basicPriceRate; }
    public double getFirstClassPriceRate() { return firstClassPriceRate; }
    public void setFirstClassPriceRate(double firstClassPriceRate) { this.firstClassPriceRate=firstClassPriceRate; }
}
