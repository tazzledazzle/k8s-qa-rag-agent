package dev.otel.demo.api.routes

import dev.otel.demo.api.plugins.configureRouting
import dev.otel.demo.api.plugins.configureSerialization
import io.ktor.client.request.get
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.client.statement.bodyAsText
import io.ktor.http.ContentType
import io.ktor.http.HttpHeaders
import io.ktor.http.HttpStatusCode
import io.ktor.server.testing.testApplication
import io.ktor.server.routing.routing
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Test

class ChatRoutesTest {
    @Test
    fun `GET chat returns 405 Method Not Allowed proving POST chat route is registered`() = testApplication {
        application {
            configureSerialization()
            configureRouting()
        }
        val response = client.get("/chat")
        assertEquals(405, response.status.value, "GET /chat should be 405 (route exists, POST only); 404 means route missing or wrong server")
    }

    // Note: Rate limiting behavior depends on process env (CHAT_RATE_LIMIT_ENABLED / CHAT_RATE_LIMIT_PER_MINUTE)
    // and Temporal/agent availability, so it is exercised in integration scenarios rather than strict unit tests here.

    @Test
    fun `POST chat returns 503 Service Unavailable when Temporal client fails`() = testApplication {
        application {
            configureSerialization()
            routing {
                chatRoutes(clientFactory = { throw RuntimeException("temporal down") })
            }
        }

        val response = client.post("/chat") {
            headers.append(HttpHeaders.ContentType, ContentType.Application.Json.toString())
            setBody("""{"message":"Hello"}""")
        }

        assertEquals(HttpStatusCode.ServiceUnavailable, response.status)
        val body = response.bodyAsText()
        assert(body.contains("temporal_unavailable")) {
            "Expected temporal_unavailable error in body, got: $body"
        }
    }
}
