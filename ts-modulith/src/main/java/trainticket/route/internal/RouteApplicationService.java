package trainticket.route.internal;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.UUID;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import trainticket.route.Route;
import trainticket.route.RouteInfo;
import trainticket.route.RouteOperations;
import trainticket.route.RouteResult;

@Service
@ConditionalOnProperty(name="modulith.route.enabled", havingValue="true")
class RouteApplicationService implements RouteOperations {
    private final RouteRepository repository;
    RouteApplicationService(RouteRepository repository) { this.repository=repository; }
    public RouteResult<List<Route>> all() {
        List<Route> routes=repository.all();
        return routes.isEmpty() ? new RouteResult<>(0,"No Content",null)
                : new RouteResult<>(1,"Success",routes);
    }
    public RouteResult<Route> find(String id) {
        Route route=repository.find(id);
        return route==null ? new RouteResult<>(0,"No content with the routeId",null)
                : new RouteResult<>(1,"Success",route);
    }
    public RouteResult<List<Route>> between(String start,String end) {
        List<Route> result=new ArrayList<>();
        for (Route route:repository.all()) {
            List<String> stations=route.getStations();
            if (stations.contains(start) && stations.contains(end) &&
                    stations.indexOf(start)<stations.indexOf(end)) result.add(route);
        }
        return result.isEmpty() ? new RouteResult<>(0,"No routes with the startId and terminalId",null)
                : new RouteResult<>(1,"Success",result);
    }
    public RouteResult<Route> save(RouteInfo info) {
        String[] stations=info.getStationList().split(",");
        String[] distances=info.getDistanceList().split(",");
        if (stations.length!=distances.length)
            return new RouteResult<>(0,"Station Number Not Equal To Distance Number",null);
        List<Integer> parsed=new ArrayList<>();
        for (String distance:distances) parsed.add(Integer.parseInt(distance));
        boolean create=info.getId()==null || info.getId().length()<10;
        String id=create ? UUID.randomUUID().toString() : info.getId();
        Route route=new Route(id,Arrays.asList(stations),parsed,info.getStartStation(),info.getEndStation());
        repository.save(route);
        return new RouteResult<>(1,create ? "Save Success" : "Modify success",route);
    }
    public RouteResult<String> delete(String id) {
        repository.delete(id);
        return repository.find(id)==null ? new RouteResult<>(1,"Delete Success",id)
                : new RouteResult<>(0,"Delete failed, Reason unKnown with this routeId",id);
    }
}
