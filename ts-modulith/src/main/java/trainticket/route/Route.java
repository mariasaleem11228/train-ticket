package trainticket.route;

import java.util.List;

/** JSON contract of the deployed Route catalogue. */
public class Route {
    private String id;
    private List<String> stations;
    private List<Integer> distances;
    private String startStationId;
    private String terminalStationId;
    public Route() { }
    public Route(String id, List<String> stations, List<Integer> distances,
                 String startStationId, String terminalStationId) {
        this.id=id; this.stations=stations; this.distances=distances;
        this.startStationId=startStationId; this.terminalStationId=terminalStationId;
    }
    public String getId() { return id; }
    public void setId(String id) { this.id=id; }
    public List<String> getStations() { return stations; }
    public void setStations(List<String> stations) { this.stations=stations; }
    public List<Integer> getDistances() { return distances; }
    public void setDistances(List<Integer> distances) { this.distances=distances; }
    public String getStartStationId() { return startStationId; }
    public void setStartStationId(String startStationId) { this.startStationId=startStationId; }
    public String getTerminalStationId() { return terminalStationId; }
    public void setTerminalStationId(String terminalStationId) { this.terminalStationId=terminalStationId; }
}
