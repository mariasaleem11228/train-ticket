package trainticket.auth;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import jakarta.servlet.DispatcherType;

@Configuration
public class SecurityConfiguration {
    @Bean
    SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        String stations = "/api/v1/stationservice/stations";
        return http.httpBasic(AbstractHttpConfigurer::disable)
                .csrf(AbstractHttpConfigurer::disable)
                .cors(Customizer.withDefaults())
                .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .authorizeHttpRequests(auth -> auth
                    .dispatcherTypeMatchers(DispatcherType.ERROR).permitAll()
                    .requestMatchers("/error").permitAll()
                    .requestMatchers(HttpMethod.POST, stations).hasRole("ADMIN")
                    .requestMatchers(HttpMethod.PUT, stations).hasRole("ADMIN")
                    .requestMatchers(HttpMethod.DELETE, stations).hasRole("ADMIN")
                    .requestMatchers(HttpMethod.POST, "/api/v1/orderservice/order/admin").hasRole("ADMIN")
                    .requestMatchers(HttpMethod.PUT, "/api/v1/orderservice/order/admin").hasRole("ADMIN")
                    .requestMatchers(HttpMethod.POST, "/api/v1/orderservice/order").hasAnyRole("ADMIN", "USER")
                    .requestMatchers(HttpMethod.PUT, "/api/v1/orderservice/order").hasAnyRole("ADMIN", "USER")
                    .requestMatchers(HttpMethod.DELETE, "/api/v1/orderservice/order").hasAnyRole("ADMIN", "USER")
                    .requestMatchers(HttpMethod.POST, "/api/v1/orderOtherService/orderOther/admin").hasRole("ADMIN")
                    .requestMatchers(HttpMethod.PUT, "/api/v1/orderOtherService/orderOther/admin").hasRole("ADMIN")
                    .requestMatchers(HttpMethod.POST, "/api/v1/orderOtherService/orderOther").hasAnyRole("ADMIN", "USER")
                    .requestMatchers(HttpMethod.PUT, "/api/v1/orderOtherService/orderOther").hasAnyRole("ADMIN", "USER")
                    .requestMatchers(HttpMethod.DELETE, "/api/v1/orderOtherService/orderOther").hasAnyRole("ADMIN", "USER")
                    .requestMatchers(HttpMethod.PUT, "/api/v1/travelservice/trips").hasRole("ADMIN")
                    .requestMatchers(HttpMethod.DELETE, "/api/v1/travelservice/trips/*").hasRole("ADMIN")
                    .requestMatchers("/api/v1/executeservice/**").hasAnyRole("ADMIN", "USER")
                    .requestMatchers("/api/v1/paymentservice/**").hasAnyRole("ADMIN", "USER")
                    .requestMatchers("/api/v1/inside_pay_service/**").hasAnyRole("ADMIN", "USER")
                    .requestMatchers("/api/v1/cancelservice/**").hasAnyRole("ADMIN", "USER")
                    .requestMatchers("/api/v1/rebookservice/**").hasAnyRole("ADMIN", "USER")
                    .requestMatchers("/api/v1/assuranceservice/**").hasRole("USER")
                    .requestMatchers("/api/v1/consignpriceservice/**").hasAnyRole("ADMIN", "USER")
                    .requestMatchers("/api/v1/consignservice/**").hasAnyRole("ADMIN", "USER")
                    .requestMatchers("/api/v1/waitorderservice/**").hasAnyRole("ADMIN", "USER")
                    .requestMatchers(HttpMethod.GET, "/api/v1/users").hasRole("ADMIN")
                    .requestMatchers(HttpMethod.DELETE, "/api/v1/users/*").hasRole("ADMIN")
                    .requestMatchers(HttpMethod.GET, "/api/v1/adminbasicservice/adminbasic/contacts", "/api/v1/adminbasicservice/adminbasic/stations", "/api/v1/adminbasicservice/adminbasic/trains", "/api/v1/adminbasicservice/adminbasic/configs", "/api/v1/adminbasicservice/adminbasic/prices").permitAll()
                    .requestMatchers("/api/v1/adminbasicservice/**").hasRole("ADMIN")
                    .requestMatchers("/api/v1/adminrouteservice/**").hasRole("ADMIN")
                    .requestMatchers("/api/v1/admintravelservice/**").hasRole("ADMIN")
                    .requestMatchers("/api/v1/adminorderservice/**").hasRole("ADMIN")
                    .requestMatchers("/api/v1/adminuserservice/**").hasRole("ADMIN")
                    .requestMatchers("/getVoucher").permitAll()
                    .requestMatchers("/news-service/**", "/news-service").permitAll()
                    .requestMatchers("/office/**", "/office").permitAll()
                    .requestMatchers("/api/v1/avatar", "/api/v1/avatar/").permitAll()
                    .requestMatchers("/api/v1/fooddeliveryservice/**").permitAll()
                    .requestMatchers("/api/v1/ticketinfoservice/**").permitAll()
                    .requestMatchers("/api/v1/users/login", "/api/v1/auth", "/api/v1/auth/hello").permitAll()
                    .requestMatchers("/api/v1/orderOtherService/orderOther/**").permitAll()
                    .requestMatchers("/api/v1/orderservice/order/**").permitAll()
                    .requestMatchers("/api/v1/stationservice/**", "/api/v1/configservice/**", "/api/v1/seatservice/**", "/api/v1/trainservice/**", "/api/v1/routeservice/**", "/api/v1/priceservice/**", "/api/v1/basicservice/**", "/api/v1/travelservice/**", "/api/v1/travel2service/**", "/api/v1/routeplanservice/**", "/api/v1/travelplanservice/**", "/api/v1/contactservice/**", "/api/v1/preserveservice/**", "/api/v1/preserveotherservice/**", "/api/v1/foodmapservice/**", "/api/v1/foodservice/**", "/api/v1/notifyservice/**", "/api/v1/verifycode/**", "/api/v1/userservice/users/**", "/api/v1/userservice/users",
                            "/actuator/health", "/actuator/modulith").permitAll()
                    .requestMatchers("/api/v1/securityservice/**").hasAnyRole("ADMIN", "USER")
                    .anyRequest().authenticated())
                .addFilterBefore(new LegacyJwtFilter(), UsernamePasswordAuthenticationFilter.class)
                .build();
    }

    @Bean
    WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurer() {
            @Override public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**").allowedOrigins("*").allowedMethods("*")
                        .allowedHeaders("*").allowCredentials(false).maxAge(3600);
            }
        };
    }
}
