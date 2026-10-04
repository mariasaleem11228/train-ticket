package trainticket.food;

/** Published order operation for booking workflows. */
public interface FoodOperations {
    FoodResult<?> create(FoodOrder input);
}
