package trainticket.notification.internal;

import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.HttpHeaders;
import org.springframework.web.bind.annotation.*;
import trainticket.notification.NotifyInfo;

@RestController
@ConditionalOnProperty(name="modulith.notification.enabled",havingValue="true")
@RequestMapping("/api/v1/notifyservice")
class NotificationController {
    private final NotificationEmailService email;
    private final RabbitTemplate rabbit;
    private final String queue;
    private final String testTo;
    NotificationController(NotificationEmailService email,RabbitTemplate rabbit,
                           @Value("${modulith.notification.queue}") String queue,
                           @Value("${modulith.notification.test-to}") String testTo) {
        this.email=email;this.rabbit=rabbit;this.queue=queue;this.testTo=testTo;
    }
    @GetMapping("/welcome") String welcome() { return "Welcome to [ Notification Service ] !"; }
    @GetMapping("/test_send_mq") boolean testMq() {
        email.guard();rabbit.convertAndSend(queue,"test");return true;
    }
    @GetMapping("/test_send_mail") boolean testMail() {
        NotifyInfo info=new NotifyInfo(null,null,testTo,"111-111-111","h10g","Test","Test",
                "Sat May 04 07:00:00 CST 2013","Wed Jul 21 09:49:44 CST 2021","1","1102","100");
        email.send("preserve",info);return true;
    }
    @PostMapping("/notification/preserve_success") boolean preserve(@RequestBody NotifyInfo info,@RequestHeader HttpHeaders headers) {
        return email.send("preserve",info);
    }
    @PostMapping("/notification/order_create_success") boolean created(@RequestBody NotifyInfo info,@RequestHeader HttpHeaders headers) {
        return email.send("create",info);
    }
    @PostMapping("/notification/order_changed_success") boolean changed(@RequestBody NotifyInfo info,@RequestHeader HttpHeaders headers) {
        return email.send("changed",info);
    }
    @PostMapping("/notification/order_cancel_success") boolean cancelled(@RequestBody NotifyInfo info,@RequestHeader HttpHeaders headers) {
        return email.send("cancel",info);
    }
}
