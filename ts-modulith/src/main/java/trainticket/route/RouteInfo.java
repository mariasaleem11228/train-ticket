package trainticket.route;

/** Deployed create/modify request, with comma-separated stations and distances. */
public class RouteInfo {
    private String id;
    private String startStation;
    private String endStation;
    private String stationList;
    private String distanceList;
    public String getId() { return id; }
    public void setId(String id) { this.id=id; }
    public String getStartStation() { return startStation; }
    public void setStartStation(String startStation) { this.startStation=startStation; }
    public String getEndStation() { return endStation; }
    public void setEndStation(String endStation) { this.endStation=endStation; }
    public String getStationList() { return stationList; }
    public void setStationList(String stationList) { this.stationList=stationList; }
    public String getDistanceList() { return distanceList; }
    public void setDistanceList(String distanceList) { this.distanceList=distanceList; }
}
