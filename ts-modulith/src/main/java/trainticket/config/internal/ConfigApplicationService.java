package trainticket.config.internal;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import trainticket.config.Config;
import trainticket.config.ConfigOperations;
import trainticket.config.ConfigResult;
import java.util.List;

/** Behavior and response messages from the deployed 0.2.0 Config service. */
@Service
@ConditionalOnProperty(name="modulith.config.enabled", havingValue="true")
class ConfigApplicationService implements ConfigOperations {
    private final ConfigRepository repository;
    ConfigApplicationService(ConfigRepository repository) { this.repository = repository; }

    public ConfigResult<List<Config>> all() {
        List<Config> configs = repository.all();
        return configs.isEmpty() ? new ConfigResult<>(0, "No content", null)
                : new ConfigResult<>(1, "Find all  config success", configs);
    }
    public ConfigResult<Config> find(String name) {
        Config config = repository.find(name);
        return config == null ? new ConfigResult<>(0, "No content", null)
                : new ConfigResult<>(1, "Success", config);
    }
    public ConfigResult<Config> create(Config config) {
        if (repository.find(config.getName()) != null)
            return new ConfigResult<>(0, "Config " + config.getName() + " already exists.", null);
        Config saved = copy(config);
        repository.save(saved);
        return new ConfigResult<>(1, "Create success", saved);
    }
    public ConfigResult<Config> update(Config config) {
        if (repository.find(config.getName()) == null)
            return new ConfigResult<>(0, "Config " + config.getName() + " doesn't exist.", null);
        Config saved = copy(config);
        repository.save(saved);
        return new ConfigResult<>(1, "Update success", saved);
    }
    public ConfigResult<Config> delete(String name) {
        Config existing = repository.find(name);
        if (existing == null)
            return new ConfigResult<>(0, "Config " + name + " doesn't exist.", null);
        repository.delete(name);
        return new ConfigResult<>(1, "Delete success", existing);
    }
    private Config copy(Config config) {
        return new Config(config.getName(), config.getValue(), config.getDescription());
    }
}
