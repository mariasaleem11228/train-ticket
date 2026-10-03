package trainticket.runtime;

import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.DeserializationContext;
import com.fasterxml.jackson.databind.JsonDeserializer;
import com.fasterxml.jackson.databind.util.StdDateFormat;
import java.io.IOException;
import java.text.ParseException;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.Date;

/** Accepts the date format sent by the existing ticket reservation UI. */
public class LegacyDepartureDateDeserializer extends JsonDeserializer<Date> {
    private static final DateTimeFormatter UI_FORMAT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    @Override
    public Date deserialize(JsonParser parser, DeserializationContext context) throws IOException {
        String value = parser.getValueAsString();
        if (value == null) return (Date) context.handleUnexpectedToken(Date.class, parser);
        try {
            return StdDateFormat.instance.parse(value);
        } catch (ParseException ignored) {
            try {
                return Date.from(LocalDateTime.parse(value, UI_FORMAT).toInstant(ZoneOffset.UTC));
            } catch (DateTimeParseException invalid) {
                return (Date) context.handleWeirdStringValue(Date.class, value, "Expected ISO date or yyyy-MM-dd HH:mm:ss");
            }
        }
    }
}
