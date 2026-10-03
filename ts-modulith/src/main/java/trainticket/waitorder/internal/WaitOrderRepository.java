package trainticket.waitorder.internal;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Repository;

import java.sql.*;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

@Repository
@ConditionalOnProperty(name="modulith.wait-order.enabled", havingValue="true")
class WaitOrderRepository {
    private final String url,user,password;
    WaitOrderRepository(@Value("${modulith.wait-order.jdbc-url}") String url,
                        @Value("${modulith.wait-order.username}") String user,
                        @Value("${modulith.wait-order.password}") String password) {
        this.url=url;this.user=user;this.password=password;
    }

    private Connection connect() throws SQLException {
        Connection db=DriverManager.getConnection(url,user,password);
        try (Statement statement=db.createStatement()) {
            statement.executeUpdate("CREATE TABLE IF NOT EXISTS wait_list_order ("
                +"id VARCHAR(36) PRIMARY KEY, travel_time DATETIME(3), account_id VARCHAR(36),"
                +"contacts_id VARCHAR(36), contacts_name VARCHAR(255), contacts_document_type INT,"
                +"contacts_document_number VARCHAR(255), train_number VARCHAR(64), seat_type INT,"
                +"from_station VARCHAR(255), to_station VARCHAR(255), price VARCHAR(64),"
                +"wait_util_time DATETIME(3), created_time DATETIME(3), status INT,"
                +"dedup_key CHAR(64) NOT NULL UNIQUE,"
                +"INDEX idx_wait_account (account_id), INDEX idx_wait_status (status,wait_util_time))");
        } catch (SQLException error) { db.close(); throw error; }
        return db;
    }

    List<WaitOrderRecord> all() {
        try (Connection db=connect(); PreparedStatement sql=db.prepareStatement(
                "SELECT * FROM wait_list_order ORDER BY created_time,id"); ResultSet rows=sql.executeQuery()) {
            List<WaitOrderRecord> result=new ArrayList<>();
            while (rows.next())result.add(map(rows));
            return result;
        } catch (SQLException error) { throw new IllegalStateException("WaitOrder read failed",error); }
    }

    boolean createIfAbsent(WaitOrderRecord order) {
        try (Connection db=connect()) {
            db.setAutoCommit(false);
            try (PreparedStatement lock=db.prepareStatement(
                    "SELECT id FROM wait_list_order WHERE account_id=? AND contacts_id=? "
                    +"AND train_number=? AND travel_time=? AND from_station=? AND to_station=? FOR UPDATE")) {
                lock.setString(1,order.accountId());lock.setString(2,order.contactsId());
                lock.setString(3,order.trainNumber());lock.setTimestamp(4,new Timestamp(order.travelTime().getTime()));
                lock.setString(5,order.from());lock.setString(6,order.to());
                try (ResultSet rows=lock.executeQuery()) {
                    if (rows.next()) { db.rollback();return false; }
                }
            }
            try (PreparedStatement sql=db.prepareStatement("INSERT INTO wait_list_order "
                    +"(id,travel_time,account_id,contacts_id,train_number,seat_type,from_station,to_station,price,wait_util_time,created_time,status,dedup_key) "
                    +"VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)")) {
                sql.setString(1,order.id());sql.setTimestamp(2,new Timestamp(order.travelTime().getTime()));
                sql.setString(3,order.accountId());sql.setString(4,order.contactsId());
                sql.setString(5,order.trainNumber());sql.setInt(6,order.seatType());
                sql.setString(7,order.from());sql.setString(8,order.to());sql.setString(9,order.price());
                sql.setTimestamp(10,new Timestamp(order.waitUtilTime().getTime()));
                sql.setTimestamp(11,new Timestamp(order.createdTime().getTime()));sql.setInt(12,order.status());
                sql.setString(13,dedup(order));
                sql.executeUpdate();
            }
            db.commit();return true;
        } catch (SQLIntegrityConstraintViolationException duplicate) { return false; }
          catch (SQLException error) { throw new IllegalStateException("WaitOrder save failed",error); }
    }

    private String dedup(WaitOrderRecord order) {
        try {
            byte[] raw=(order.accountId()+"\u0000"+order.contactsId()+"\u0000"+order.trainNumber()
                +"\u0000"+order.travelTime().getTime()+"\u0000"+order.from()+"\u0000"+order.to())
                .getBytes(java.nio.charset.StandardCharsets.UTF_8);
            byte[] digest=java.security.MessageDigest.getInstance("SHA-256").digest(raw);
            return java.util.HexFormat.of().formatHex(digest);
        } catch (java.security.NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); }
    }

    int expire() {
        try (Connection db=connect(); PreparedStatement sql=db.prepareStatement(
                "UPDATE wait_list_order SET status=5 WHERE status IN (0,1) AND wait_util_time < CURRENT_TIMESTAMP(3)")) {
            return sql.executeUpdate();
        } catch (SQLException error) { throw new IllegalStateException("WaitOrder expiry failed",error); }
    }

    private WaitOrderRecord map(ResultSet row) throws SQLException {
        return new WaitOrderRecord(row.getString("id"),date(row,"travel_time"),row.getString("account_id"),
                row.getString("contacts_id"),row.getString("contacts_name"),row.getInt("contacts_document_type"),
                row.getString("contacts_document_number"),row.getString("train_number"),row.getInt("seat_type"),
                row.getString("from_station"),row.getString("to_station"),row.getString("price"),
                date(row,"wait_util_time"),date(row,"created_time"),row.getInt("status"));
    }
    private Date date(ResultSet row,String column) throws SQLException {
        Timestamp value=row.getTimestamp(column);return value==null?null:new Date(value.getTime());
    }
}
