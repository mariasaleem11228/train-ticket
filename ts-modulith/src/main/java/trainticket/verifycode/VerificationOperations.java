package trainticket.verifycode;

/** Published local CAPTCHA contract. */
public interface VerificationOperations {
    boolean verify(String code, String cookieValue);
}
