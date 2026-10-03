package trainticket.train.internal;

import java.util.List;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;
import trainticket.train.TrainOperations;
import trainticket.train.TrainResult;
import trainticket.train.TrainType;

@Service
@ConditionalOnProperty(name="modulith.train.enabled", havingValue="true")
class TrainApplicationService implements TrainOperations {
    private final TrainRepository repository;
    TrainApplicationService(TrainRepository repository) { this.repository = repository; }
    public TrainResult<List<TrainType>> all() {
        List<TrainType> result = repository.all();
        return result.isEmpty() ? new TrainResult<>(0, "no content", result)
                : new TrainResult<>(1, "success", result);
    }
    public TrainResult<TrainType> find(String id) {
        TrainType train = repository.find(id);
        return train == null ? new TrainResult<>(0, "here is no TrainType with the trainType id: " + id, null)
                : new TrainResult<>(1, "success", train);
    }
    public TrainResult<TrainType> create(TrainType train) {
        if (repository.find(train.getId()) != null) return new TrainResult<>(0, "train type already exist", train);
        repository.save(train);
        return new TrainResult<>(1, "create success", null);
    }
    public TrainResult<Boolean> update(TrainType train) {
        if (repository.find(train.getId()) == null)
            return new TrainResult<>(0, "there is no trainType with the trainType id", false);
        repository.save(train);
        return new TrainResult<>(1, "update success", true);
    }
    public TrainResult<Boolean> delete(String id) {
        if (repository.find(id) == null) return new TrainResult<>(0, "there is no train according to id", null);
        repository.delete(id);
        return new TrainResult<>(1, "delete success", true);
    }
}
