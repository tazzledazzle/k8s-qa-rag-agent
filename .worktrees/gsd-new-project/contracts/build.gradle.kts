plugins {
    kotlin("jvm") version "1.9.24"
}

kotlin {
    jvmToolchain(17)
}

repositories {
    mavenCentral()
}

dependencies {
    implementation("io.temporal:temporal-sdk:1.24.0")
}
