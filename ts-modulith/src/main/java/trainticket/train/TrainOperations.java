package trainticket.train;

import java.util.List;

/** Exported Train catalogue API for future Travel and administration modules. */
public interface TrainOperations {
    TrainResult<List<TrainType>> all();
    TrainResult<TrainType> find(String id);
    TrainResult<TrainType> create(TrainType train);
    TrainResult<Boolean> update(TrainType train);
    TrainResult<Boolean> delete(String id);
}
