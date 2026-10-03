package trainticket.auth;

import io.jsonwebtoken.*;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.filter.OncePerRequestFilter;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.*;
import java.io.IOException;
import java.util.*;
import java.util.stream.Collectors;

/** Adapter for the existing benchmark's signed JWT contract. */
class LegacyJwtFilter extends OncePerRequestFilter {
    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {
        String header = request.getHeader("Authorization");
        if (header != null && header.startsWith("Bearer ")) {
            try {
                Claims claims = Jwts.parser().setSigningKey(Base64.getEncoder().encodeToString("secret".getBytes("UTF-8")))
                        .parseClaimsJws(header.substring(7)).getBody();
                if (claims.getExpiration() == null || claims.getExpiration().before(new Date())) throw new IllegalArgumentException("Expired token");
                List<?> roles = claims.get("roles", List.class);
                if (roles == null) throw new IllegalArgumentException("Missing roles");
                SecurityContextHolder.getContext().setAuthentication(new UsernamePasswordAuthenticationToken(
                        claims.getSubject(), "", roles.stream().map(Object::toString)
                        .map(SimpleGrantedAuthority::new).collect(Collectors.toList())));
            } catch (JwtException | IllegalArgumentException ex) {
                SecurityContextHolder.clearContext();
                response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
                return;
            }
        }
        chain.doFilter(request, response);
    }
}
