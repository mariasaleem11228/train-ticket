package trainticket.fooddelivery.internal;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Repository;
import trainticket.fooddelivery.FoodDeliveryOrder;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Repository
@ConditionalOnProperty(name="modulith.fooddelivery.enabled",havingValue="true")
class FoodDeliveryRepository {
    private static final TypeReference<List<Map<String,Object>>> FOODS = new TypeReference<>() {};
    private final String url;
    private final String user;
    private final String password;
    private final ObjectMapper mapper;

    FoodDeliveryRepository(@Value("${modulith.fooddelivery.jdbc-url}") String url,
                           @Value("${modulith.fooddelivery.username}") String user,
                           @Value("${modulith.fooddelivery.password}") String password,
                           ObjectMapper mapper) {
        this.url=url;this.user=user;this.password=password;this.mapper=mapper;
    }

    private Connection connect() throws SQLException {
        Connection connection=DriverManager.getConnection(url,user,password);
        try (Statement statement=connection.createStatement()) {
            statement.executeUpdate("CREATE TABLE IF NOT EXISTS food_delivery_order ("
                    + "id VARCHAR(36) PRIMARY KEY, station_food_store_id VARCHAR(36),"
                    + "food_list LONGTEXT, trip_id VARCHAR(64), seat_no INT,"
                    + "created_time VARCHAR(64), delivery_time VARCHAR(64), delivery_fee DOUBLE)");
        } catch (SQLException error) {
            connection.close();
            throw error;
        }
        return connection;
    }

    FoodDeliveryOrder byId(String id) {
        try (Connection connection=connect();
             PreparedStatement statement=connection.prepareStatement(
                     "SELECT * FROM food_delivery_order WHERE id=?")) {
            statement.setString(1,id);
            try (ResultSet rows=statement.executeQuery()) {
                return rows.next()?map(rows):null;
            }
        } catch (Exception error) { throw new IllegalStateException("Food delivery read failed",error); }
    }

    List<FoodDeliveryOrder> all() { return list(null); }
    List<FoodDeliveryOrder> byStore(String store) { return list(store); }

    private List<FoodDeliveryOrder> list(String store) {
        String sql=store==null?"SELECT * FROM food_delivery_order ORDER BY id":
                "SELECT * FROM food_delivery_order WHERE station_food_store_id=? ORDER BY id";
        try (Connection connection=connect();PreparedStatement statement=connection.prepareStatement(sql)) {
            if (store!=null)statement.setString(1,store);
            try (ResultSet rows=statement.executeQuery()) {
                List<FoodDeliveryOrder> result=new ArrayList<>();
                while (rows.next())result.add(map(rows));
                return result;
            }
        } catch (Exception error) { throw new IllegalStateException("Food delivery list failed",error); }
    }

    void save(FoodDeliveryOrder order) {
        String sql="INSERT INTO food_delivery_order VALUES (?,?,?,?,?,?,?,?) "
                + "ON DUPLICATE KEY UPDATE station_food_store_id=VALUES(station_food_store_id),"
                + "food_list=VALUES(food_list),trip_id=VALUES(trip_id),seat_no=VALUES(seat_no),"
                + "created_time=VALUES(created_time),delivery_time=VALUES(delivery_time),"
                + "delivery_fee=VALUES(delivery_fee)";
        try (Connection connection=connect();PreparedStatement statement=connection.prepareStatement(sql)) {
            statement.setString(1,order.id());
            statement.setString(2,order.stationFoodStoreId());
            statement.setString(3,mapper.writeValueAsString(order.foodList()));
            statement.setString(4,order.tripId());
            statement.setInt(5,order.seatNo());
            statement.setString(6,order.createdTime());
            statement.setString(7,order.deliveryTime());
            statement.setDouble(8,order.deliveryFee());
            statement.executeUpdate();
        } catch (Exception error) { throw new IllegalStateException("Food delivery save failed",error); }
    }

    void delete(String id) {
        try (Connection connection=connect();PreparedStatement statement=connection.prepareStatement(
                "DELETE FROM food_delivery_order WHERE id=?")) {
            statement.setString(1,id);statement.executeUpdate();
        } catch (Exception error) { throw new IllegalStateException("Food delivery delete failed",error); }
    }

    private FoodDeliveryOrder map(ResultSet row) throws Exception {
        return new FoodDeliveryOrder(row.getString("id"),row.getString("station_food_store_id"),
                mapper.readValue(row.getString("food_list"),FOODS),row.getString("trip_id"),
                row.getInt("seat_no"),row.getString("created_time"),
                row.getString("delivery_time"),row.getDouble("delivery_fee"));
    }
}
