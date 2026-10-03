package trainticket.basic;

import java.util.Map;
import trainticket.train.TrainType;

public record BasicTravelData(boolean status, double percent, TrainType trainType,
                              Map<String,String> prices) {}
