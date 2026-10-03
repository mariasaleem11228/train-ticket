package trainticket.travelplan;

import java.util.Date;

public record TransferQuery(String fromStationName, String viaStationName,
                            String toStationName, Date travelDate, String trainType) { }
