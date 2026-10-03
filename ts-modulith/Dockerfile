FROM eclipse-temurin:21-jre@sha256:d7051a45dd955e4d5d1db4d3f4269fe13d1c6dff8cc6b7ef89fc8577b96c1982
WORKDIR /app
COPY target/ts-modulith-0.1.0.jar app.jar
EXPOSE 18080
ENTRYPOINT ["java", "-XX:+UseSerialGC", "-Xmx256m", "-jar", "/app/app.jar"]
