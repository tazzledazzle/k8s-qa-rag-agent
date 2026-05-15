package dev.otel.demo.api.routes

import io.ktor.client.request.get
import io.ktor.client.statement.bodyAsText
import io.ktor.serialization.jackson.jackson
import io.ktor.server.testing.testApplication
import io.ktor.server.application.install
import io.ktor.server.plugins.contentnegotiation.ContentNegotiation
import io.ktor.server.routing.routing
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class HealthRoutesTest {
    @Test
    fun `GET health returns JSON with status and service`() = testApplication {
        application {
            install(ContentNegotiation) {
                jackson()
            }
            routing {
                healthRoutes()
            }
        }
        val response = client.get("/health")
        assertEquals(200, response.status.value)
        val json = response.bodyAsText()
        assert(json.contains("ok") && json.contains("otel-demo-api")) { "Expected status and service in body: $json" }
    }

    @Test
    fun `GET ready returns 200 when Temporal probe succeeds`() = testApplication {
        application {
            install(ContentNegotiation) {
                jackson()
            }
            routing {
                healthRoutes(temporalProbe = { true })
            }
        }
        val response = client.get("/ready")
        assertEquals(200, response.status.value)
        val json = response.bodyAsText()
        assert(json.contains("ready") && json.contains("available")) {
            "Expected ready status and temporal available in body: $json"
        }
    }

    @Test
    fun `GET ready returns 503 when Temporal probe fails`() = testApplication {
        application {
            install(ContentNegotiation) {
                jackson()
            }
            routing {
                healthRoutes(temporalProbe = { false })
            }
        }
        val response = client.get("/ready")
        assertEquals(503, response.status.value)
        val json = response.bodyAsText()
        assert(json.contains("degraded") && json.contains("unavailable")) {
            "Expected degraded status and temporal unavailable in body: $json"
        }
    }
}
