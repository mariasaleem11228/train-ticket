package trainticket;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.modulith.Modulithic;

@Modulithic(systemName="Train Ticket")
@SpringBootApplication
@org.springframework.scheduling.annotation.EnableScheduling
public class ModulithApplication {
    public static void main(String[] args) {
        SpringApplication.run(ModulithApplication.class, args);
    }
}
