package dev.otel.demo.api

import dev.otel.demo.api.plugins.configureRouting
import dev.otel.demo.api.plugins.configureSerialization
import io.ktor.server.application.Application
import io.ktor.server.engine.embeddedServer
import io.ktor.server.netty.Netty
import java.net.BindException
import java.net.ServerSocket

fun main() {
    val otelEndpoint = System.getenv("OTEL_EXPORTER_OTLP_ENDPOINT") ?: "http://localhost:4317"
    initOpenTelemetry("otel-demo-api", otelEndpoint)
    val port = resolvePortWithDiscovery()
    try {
        System.err.println("API starting on http://0.0.0.0:$port (POST /chat, GET /health)")
        embeddedServer(Netty, port = port) {
            configureSerialization()
            configureRouting()
        }.start(wait = true)
    } catch (e: BindException) {
        System.err.println("API could not bind to port $port. Set API_PORT to a different port or stop the other process.")
        throw e
    }
}

/**
 * Port resolution (Phase 1 preferred defaults):
 * - When API_PORT is set: use it as-is (parse fallback to 8080).
 * - When API_PORT is unset: use 8080; fail with a clear message if 8080 is in use.
 */
private fun resolvePortWithDiscovery(): Int {
    val envPort = System.getenv("API_PORT")
    val port = if (envPort != null) envPort.toIntOrNull() ?: 8080 else 8080
    if (port == 8080 && !isPortAvailable(8080)) {
        System.err.println("API could not bind to port 8080. Set API_PORT to a different port or stop the other process.")
        throw IllegalStateException("Port 8080 is in use. Set API_PORT to override.")
    }
    return port
}

private fun isPortAvailable(port: Int): Boolean {
    return try {
        ServerSocket(port).use { socket ->
            socket.reuseAddress = true
        }
        true
    } catch (e: Exception) {
        false
    }
}
