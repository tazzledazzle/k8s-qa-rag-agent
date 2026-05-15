plugins {
    kotlin("jvm") version "1.9.24"
    application
}

application {
    mainClass.set("dev.otel.demo.api.MainKt")
}

kotlin {
    jvmToolchain(17)
}

repositories {
    mavenCentral()
}

dependencies {
    implementation(project(":contracts"))
    implementation("io.ktor:ktor-server-core-jvm:2.3.9")
    implementation("io.ktor:ktor-server-netty-jvm:2.3.9")
    implementation("io.ktor:ktor-server-content-negotiation-jvm:2.3.9")
    implementation("io.ktor:ktor-serialization-jackson-jvm:2.3.9")
    implementation("com.fasterxml.jackson.module:jackson-module-kotlin:2.16.1")

    implementation("io.temporal:temporal-sdk:1.24.0")
    implementation("io.temporal:temporal-kotlin:1.24.0")

    implementation("io.opentelemetry:opentelemetry-api:1.35.0")
    implementation("io.opentelemetry:opentelemetry-sdk:1.35.0")
    implementation("io.opentelemetry:opentelemetry-exporter-otlp:1.35.0")
    implementation("io.opentelemetry.instrumentation:opentelemetry-instrumentation-annotations:2.3.0")

    testImplementation("org.jetbrains.kotlin:kotlin-test-junit5:1.9.24")
    testImplementation("io.ktor:ktor-server-test-host-jvm:2.3.9")
    testImplementation("io.ktor:ktor-client-content-negotiation-jvm:2.3.9")
    testImplementation("io.ktor:ktor-serialization-jackson-jvm:2.3.9")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}

tasks.test {
    useJUnitPlatform()
}
