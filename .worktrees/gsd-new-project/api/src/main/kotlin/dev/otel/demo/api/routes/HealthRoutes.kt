package dev.otel.demo.api.routes

import dev.otel.demo.api.TemporalHealth
import dev.otel.demo.api.models.HealthResponse
import dev.otel.demo.api.models.ReadinessResponse
import io.ktor.http.HttpStatusCode
import io.ktor.server.response.respond
import io.ktor.server.routing.Routing
import io.ktor.server.routing.get

fun Routing.healthRoutes(
    temporalProbe: () -> Boolean = { TemporalHealth.isTemporalAvailable() }
) {
    get("/health") {
        context.respond(HealthResponse(status = "ok", service = "otel-demo-api"))
    }
    get("/ready") {
        val temporalOk = temporalProbe()
        val status = if (temporalOk) "ready" else "degraded"
        val temporalStatus = if (temporalOk) "available" else "unavailable"
        val code = if (temporalOk) HttpStatusCode.OK else HttpStatusCode.ServiceUnavailable
        context.respond(
            code,
            ReadinessResponse(
                status = status,
                temporal = temporalStatus
            )
        )
    }
}
