package trainticket.voucher;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Repository;
import org.springframework.web.server.ResponseStatusException;
import trainticket.runtime.WriteOwnership;

@Repository
@ConditionalOnProperty(name = "modulith.voucher.enabled", havingValue = "true")
class VoucherRepository {
    private final String url;
    private final String user;
    private final String password;
    private final boolean writesEnabled;
    private final WriteOwnership ownership;

    VoucherRepository(@Value("${modulith.voucher.jdbc-url}") String url,
                      @Value("${modulith.voucher.username}") String user,
                      @Value("${modulith.voucher.password}") String password,
                      @Value("${modulith.voucher.writes-enabled:false}") boolean writesEnabled,
                      WriteOwnership ownership) {
        this.url = url;
        this.user = user;
        this.password = password;
        this.writesEnabled = writesEnabled;
        this.ownership = ownership;
    }

    Map<String,Object> find(String orderId) {
        String sql = "SELECT voucher_id,order_id,travelDate,contactName,trainNumber,seatNumber,startStation,destStation,price FROM voucher WHERE order_id=? LIMIT 1";
        try (Connection connection = connect(); PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1,orderId);
            try (ResultSet row = statement.executeQuery()) {
                if (!row.next()) return null;
                Map<String,Object> voucher = new LinkedHashMap<>();
                voucher.put("voucher_id",row.getInt("voucher_id"));
                voucher.put("order_id",row.getString("order_id"));
                voucher.put("travelDate",row.getString("travelDate"));
                voucher.put("contactName",row.getString("contactName"));
                voucher.put("train_number",row.getString("trainNumber"));
                voucher.put("seat_number",row.getString("seatNumber"));
                voucher.put("start_station",row.getString("startStation"));
                voucher.put("dest_station",row.getString("destStation"));
                voucher.put("price",row.getFloat("price"));
                return voucher;
            }
        } catch (SQLException ex) {
            throw new IllegalStateException("Voucher lookup failed",ex);
        }
    }

    void insert(VoucherDetails order) {
        if (!writesEnabled || !ownership.permits("voucher"))
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,"Voucher writes disabled");
        String sql = "INSERT INTO voucher (order_id,travelDate,travelTime,contactName,trainNumber,seatClass,seatNumber,startStation,destStation,price) VALUES (?,?,?,?,?,?,?,?,?,?)";
        try (Connection connection = connect(); PreparedStatement statement = connection.prepareStatement(sql)) {
            statement.setString(1,order.id());
            statement.setString(2,order.travelDate());
            statement.setString(3,order.travelTime());
            statement.setString(4,order.contactName());
            statement.setString(5,order.trainNumber());
            statement.setInt(6,order.seatClass());
            statement.setString(7,order.seatNumber());
            statement.setString(8,order.startStation());
            statement.setString(9,order.destStation());
            statement.setFloat(10,order.price());
            statement.executeUpdate();
        } catch (SQLException ex) {
            throw new IllegalStateException("Voucher insert failed",ex);
        }
    }

    private Connection connect() throws SQLException { return DriverManager.getConnection(url,user,password); }
}
