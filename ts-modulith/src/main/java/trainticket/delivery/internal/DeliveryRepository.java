package trainticket.delivery.internal;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Repository;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.UUID;

@Repository
@ConditionalOnProperty(name = "modulith.delivery.enabled", havingValue = "true")
class DeliveryRepository {
    private final String url;
    private final String user;
    private final String password;

    DeliveryRepository(@Value("${modulith.delivery.jdbc-url}") String url,
                       @Value("${modulith.delivery.username}") String user,
                       @Value("${modulith.delivery.password}") String password) {
        this.url = url;
        this.user = user;
        this.password = password;
    }

    boolean ready() {
        try (Connection connection = connect()) {
            ensureSchema(connection);
            return true;
        } catch (SQLException failure) {
            return false;
        }
    }

    void save(UUID orderId, String foodName, String storeName, String stationName) {
        try (Connection connection = connect()) {
            ensureSchema(connection);
            String sql = "INSERT INTO delivery (id,order_id,food_name,store_name,station_name) VALUES (?,?,?,?,?) "
                    + "ON DUPLICATE KEY UPDATE food_name=VALUES(food_name),store_name=VALUES(store_name),"
                    + "station_name=VALUES(station_name)";
            try (PreparedStatement statement = connection.prepareStatement(sql)) {
                statement.setString(1, UUID.randomUUID().toString());
                statement.setString(2, orderId.toString());
                statement.setString(3, foodName);
                statement.setString(4, storeName);
                statement.setString(5, stationName);
                statement.executeUpdate();
            }
        } catch (SQLException failure) {
            throw new IllegalStateException("Delivery persistence failed", failure);
        }
    }

    private Connection connect() throws SQLException {
        return DriverManager.getConnection(url, user, password);
    }

    private void ensureSchema(Connection connection) throws SQLException {
        try (Statement statement = connection.createStatement()) {
            statement.executeUpdate("CREATE TABLE IF NOT EXISTS delivery ("
                    + "id VARCHAR(36) PRIMARY KEY, order_id VARCHAR(36) NOT NULL UNIQUE,"
                    + "food_name TEXT, store_name TEXT, station_name TEXT)");
        }
    }
}
