# Multi-stage build for Kotlin service
FROM gradle:8.4-jdk21 AS builder

WORKDIR /app
COPY services/git-watcher .
RUN gradle shadowJar -x test --no-daemon

FROM eclipse-temurin:21-jre-jammy

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/build/libs/app.jar app.jar

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

CMD ["java", "-jar", "app.jar"]
