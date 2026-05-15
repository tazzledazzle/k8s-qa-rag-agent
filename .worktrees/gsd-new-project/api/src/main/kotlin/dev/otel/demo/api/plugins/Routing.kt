package dev.otel.demo.api.plugins

import dev.otel.demo.api.routes.chatRoutes
import dev.otel.demo.api.routes.healthRoutes
import io.ktor.server.application.Application
import io.ktor.server.routing.routing

fun Application.configureRouting() {
    routing {
        healthRoutes()
        chatRoutes()
    }
}
