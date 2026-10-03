package trainticket.orders;

public class OrderResult<T> {
    private final Integer status;
    private final String msg;
    private final T data;
    public OrderResult(Integer status, String msg, T data) { this.status=status; this.msg=msg; this.data=data; }
    public Integer getStatus() { return status; }
    public String getMsg() { return msg; }
    public T getData() { return data; }
}
