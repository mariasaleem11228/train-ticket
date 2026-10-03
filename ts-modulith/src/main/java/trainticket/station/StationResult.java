package trainticket.station;

/** Legacy HTTP envelope also usable without HTTP by future local callers. */
public class StationResult {
    private final int status;
    private final String msg;
    private final Object data;
    public StationResult(int status, String msg, Object data) {
        this.status = status; this.msg = msg; this.data = data;
    }
    public int getStatus() { return status; }
    public String getMsg() { return msg; }
    public Object getData() { return data; }
}
