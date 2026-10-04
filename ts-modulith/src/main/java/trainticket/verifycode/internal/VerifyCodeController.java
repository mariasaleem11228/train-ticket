package trainticket.verifycode.internal;

import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.imageio.ImageIO;
import java.awt.Color;
import java.awt.Font;
import java.awt.Graphics;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Random;
import java.util.UUID;
import trainticket.verifycode.VerificationOperations;

@RestController
@ConditionalOnProperty(name="modulith.verifycode.enabled",havingValue="true")
@RequestMapping("/api/v1/verifycode")
class VerifyCodeController implements VerificationOperations {
    private static final String COOKIE="YsbCaptcha";
    private static final int EXPIRES_SECONDS=1000;
    private static final char[] LETTERS="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789".toCharArray();
    private final Map<String,Entry> codes=new LinkedHashMap<>(16,.75f,true) {
        @Override protected boolean removeEldestEntry(Map.Entry<String,Entry> eldest) {
            return size()>1000;
        }
    };
    private record Entry(String code,long expiresAt) {}

    @GetMapping("/generate")
    void generate(HttpServletRequest request,HttpServletResponse response) throws IOException {
        BufferedImage image=new BufferedImage(60,20,BufferedImage.TYPE_INT_RGB);
        Graphics graphics=image.getGraphics();
        Random random=new Random();
        graphics.setColor(randomColor(random,200,250));graphics.fillRect(0,0,60,20);
        graphics.setFont(new Font("Times New Roman",Font.PLAIN,18));
        graphics.setColor(randomColor(random,160,200));
        for (int i=0;i<168;i++) {
            int x=random.nextInt(60),y=random.nextInt(20);
            graphics.drawLine(x,y,x+random.nextInt(12),y+random.nextInt(12));
        }
        StringBuilder code=new StringBuilder();
        for (int i=0;i<4;i++) {
            char letter=LETTERS[(int)(LETTERS.length*Math.random())];
            code.append(letter);
            graphics.setColor(new Color(20+random.nextInt(110),20+random.nextInt(110),20+random.nextInt(110)));
            graphics.drawString(String.valueOf(letter),13*i+6,16);
        }
        graphics.dispose();
        String key=key(request,response,true);
        synchronized(codes) { codes.put(key,new Entry(code.toString(),System.currentTimeMillis()+EXPIRES_SECONDS*1000L)); }
        request.getSession().setAttribute("simpleCaptcha",code.toString().toLowerCase());
        request.getSession().setAttribute("codeTime",System.currentTimeMillis());
        if (!ImageIO.write(image,"JPEG",response.getOutputStream()))
            response.getOutputStream().write("Can't generate verification code".getBytes());
    }

    @GetMapping("/verify/{verifyCode}")
    boolean verify(@PathVariable String verifyCode,HttpServletRequest request,HttpServletResponse response) {
        String key=key(request,response,false);
        return verify(verifyCode,key);
    }

    @Override public boolean verify(String verifyCode,String key) {
        // The deployed controller returns true regardless of this check. Preserve that wire contract.
        synchronized(codes) {
            Entry saved=codes.get(key);
            if (saved!=null) {
                if (saved.expiresAt()<System.currentTimeMillis())codes.remove(key);
                else {
                    codes.put(key,new Entry(saved.code(),System.currentTimeMillis()+EXPIRES_SECONDS*1000L));
                    saved.code().equalsIgnoreCase(verifyCode);
                }
            }
        }
        return true;
    }

    private String key(HttpServletRequest request,HttpServletResponse response,boolean generating) {
        Cookie found=null;
        if (request.getCookies()!=null)for (Cookie cookie:request.getCookies())
            if (COOKIE.equals(cookie.getName()))found=cookie;
        if (found!=null && !generating)return found.getValue();
        String value=UUID.randomUUID().toString().replace("-","").toUpperCase();
        Cookie cookie=new Cookie(COOKIE,value);
        cookie.setHttpOnly(true);cookie.setPath("/");cookie.setMaxAge(EXPIRES_SECONDS);
        response.addCookie(cookie);
        return value;
    }
    private Color randomColor(Random random,int min,int max) {
        return new Color(min+random.nextInt(max-min),min+random.nextInt(max-min),min+random.nextInt(max-min));
    }
}
