package trainticket.notification.internal;

import freemarker.template.Configuration;
import freemarker.template.Template;
import jakarta.mail.internet.MimeMessage;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpStatus;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;
import trainticket.notification.NotifyInfo;
import trainticket.runtime.WriteOwnership;
import java.io.StringWriter;
import java.util.HashMap;
import java.util.Map;

@Service
@ConditionalOnProperty(name="modulith.notification.enabled",havingValue="true")
class NotificationEmailService {
    private static final Logger LOG=LoggerFactory.getLogger(NotificationEmailService.class);
    private final JavaMailSender sender;
    private final Configuration templates;
    private final String from;
    private final boolean writesEnabled;
    private final WriteOwnership ownership;
    NotificationEmailService(JavaMailSender sender,
                             @Value("${modulith.notification.from}") String from,
                             @Value("${modulith.notification.writes-enabled:false}") boolean writesEnabled,
                             WriteOwnership ownership) {
        this.sender=sender;this.from=from;this.writesEnabled=writesEnabled;this.ownership=ownership;
        templates=new Configuration(Configuration.DEFAULT_INCOMPATIBLE_IMPROVEMENTS);
        templates.setClassLoaderForTemplateLoading(getClass().getClassLoader(),"templates/notification");
    }
    boolean send(String kind,NotifyInfo info) {
        guard();
        String subject=switch(kind) {
            case "preserve" -> "Preserve Success";
            case "create" -> "Order Create Success";
            case "changed" -> "Order Changed Success";
            case "cancel" -> "Order Cancel Success";
            default -> throw new IllegalArgumentException(kind);
        };
        String file=switch(kind) {
            case "preserve" -> "preserve_success.ftl";
            case "create" -> "order_create_success.ftl";
            case "changed" -> "order_changed_success.ftl";
            case "cancel" -> "order_cancel_success.ftl";
            default -> throw new IllegalArgumentException(kind);
        };
        try {
            Map<String,Object> model=new HashMap<>();
            model.put("username",info.username());model.put("startingPlace",info.startingPlace());
            model.put("endPlace",info.endPlace());model.put("startingTime",info.startingTime());
            model.put("date",info.date());model.put("seatClass",info.seatClass());
            model.put("seatNumber",info.seatNumber());model.put("price",info.price());
            model.put("orderNumber",info.orderNumber());
            Template template=templates.getTemplate(file);
            StringWriter html=new StringWriter();template.process(model,html);
            MimeMessage message=sender.createMimeMessage();
            MimeMessageHelper helper=new MimeMessageHelper(message);
            helper.setTo(info.email());helper.setText(html.toString(),true);
            helper.setFrom(from);helper.setSubject(subject);
            sender.send(message);
            return true;
        } catch (Exception error) {
            LOG.error("Notification email failed: {}",kind,error);
            return false;
        }
    }
    void guard() {
        if (!writesEnabled || !ownership.permits("notification"))
            throw new ResponseStatusException(HttpStatus.SERVICE_UNAVAILABLE,"Notification inactive");
    }
}
