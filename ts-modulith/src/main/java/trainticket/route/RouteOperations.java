package trainticket.route;

import java.util.List;

/** Published API for future journey-search and administration modules. */
public interface RouteOperations {
    RouteResult<List<Route>> all();
    RouteResult<Route> find(String id);
    RouteResult<List<Route>> between(String start, String end);
    RouteResult<Route> save(RouteInfo info);
    RouteResult<String> delete(String id);
}
