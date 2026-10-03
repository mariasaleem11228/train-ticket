package trainticket.config;

import java.util.List;

/** Public API for later Seat and administration modules. */
public interface ConfigOperations {
    ConfigResult<List<Config>> all();
    ConfigResult<Config> find(String name);
    ConfigResult<Config> create(Config config);
    ConfigResult<Config> update(Config config);
    ConfigResult<Config> delete(String name);
}
