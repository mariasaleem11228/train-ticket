package trainticket.train;

/** Wire contract of the deployed Mongo-backed Train service. */
public class TrainType {
    private String id;
    private int economyClass;
    private int confortClass;
    private int averageSpeed;

    public TrainType() { }
    public TrainType(String id, int economyClass, int confortClass, int averageSpeed) {
        this.id = id;
        this.economyClass = economyClass;
        this.confortClass = confortClass;
        this.averageSpeed = averageSpeed;
    }
    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public int getEconomyClass() { return economyClass; }
    public void setEconomyClass(int economyClass) { this.economyClass = economyClass; }
    public int getConfortClass() { return confortClass; }
    public void setConfortClass(int confortClass) { this.confortClass = confortClass; }
    public int getAverageSpeed() { return averageSpeed; }
    public void setAverageSpeed(int averageSpeed) { this.averageSpeed = averageSpeed; }
}
