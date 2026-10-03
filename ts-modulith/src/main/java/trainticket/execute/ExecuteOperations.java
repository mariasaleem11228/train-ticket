package trainticket.execute;

public interface ExecuteOperations {
    ExecuteResult execute(String orderId);
    ExecuteResult collect(String orderId);
}
