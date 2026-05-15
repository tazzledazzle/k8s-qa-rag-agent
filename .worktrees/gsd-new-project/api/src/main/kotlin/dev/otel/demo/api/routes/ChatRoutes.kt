package dev.otel.demo.api.routes

import dev.otel.demo.api.AgentWorkflowClient
import dev.otel.demo.api.TemporalClientFactory
import dev.otel.demo.api.models.ChatRequest
import dev.otel.demo.api.models.ChatResponse
import io.ktor.http.HttpStatusCode
import io.ktor.server.response.respond
import io.opentelemetry.api.GlobalOpenTelemetry
import io.opentelemetry.api.trace.Span
import io.opentelemetry.api.trace.SpanKind
import io.opentelemetry.api.trace.StatusCode
import io.ktor.server.request.receive
import io.ktor.server.routing.Routing
import io.ktor.server.routing.post

private fun logStructured(
    service: String,
    traceId: String,
    spanId: String,
    outcome: String,
    workflowId: String? = null,
    taskQueue: String? = null
) {
    val extra = mutableListOf<String>()
    workflowId?.let { extra.add(""""workflow_id":"$it"""") }
    taskQueue?.let { extra.add(""""task_queue":"$it"""") }
    val suffix = if (extra.isEmpty()) "" else "," + extra.joinToString(",")
    System.err.println("""{"service":"$service","trace_id":"$traceId","span_id":"$spanId","outcome":"$outcome"$suffix}""")
}

private class SimpleChatRateLimiter(private val maxPerMinute: Long) {
    private var windowStartMillis: Long = System.currentTimeMillis()
    private var count: Long = 0

    @Synchronized
    fun allowRequest(): Boolean {
        val now = System.currentTimeMillis()
        val windowMillis = 60_000L
        if (now - windowStartMillis >= windowMillis) {
            windowStartMillis = now
            count = 0
        }
        if (count >= maxPerMinute) {
            return false
        }
        count += 1
        return true
    }
}

fun Routing.chatRoutes(
    clientFactory: () -> AgentWorkflowClient = { TemporalClientFactory.create() }
) {
    val tracer = GlobalOpenTelemetry.get().getTracer("otel-demo-api", "1.0")
    val authEnabled = (System.getenv("API_AUTH_ENABLED") ?: "false").trim().lowercase() in setOf("1", "true")
    val expectedToken = System.getenv("API_AUTH_TOKEN")?.trim().takeUnless { it.isNullOrEmpty() }
    val rateLimitEnabled = (System.getenv("CHAT_RATE_LIMIT_ENABLED") ?: "false").trim().lowercase() in setOf("1", "true")
    val rateLimitPerMinute = (System.getenv("CHAT_RATE_LIMIT_PER_MINUTE") ?: "0").toLongOrNull()?.takeIf { it > 0 }
    val rateLimiter = SimpleChatRateLimiter(rateLimitPerMinute ?: Long.MAX_VALUE)

    post("/chat") {
        val ctx = context
        val span = tracer.spanBuilder("POST /chat").setSpanKind(SpanKind.SERVER).startSpan()
        span.setAttribute("message.type", "chat")
        try {
            span.makeCurrent().use {
                val sc = Span.current().spanContext
                logStructured("otel-demo-api", sc.traceId, sc.spanId, "start")
                if (authEnabled) {
                    val authHeader = ctx.request.headers["Authorization"]?.trim().orEmpty()
                    val token = if (authHeader.startsWith("Bearer ")) {
                        authHeader.removePrefix("Bearer ").trim()
                    } else {
                        authHeader
                    }
                    if (expectedToken.isNullOrEmpty() || token != expectedToken) {
                        span.recordException(IllegalStateException("unauthorized"))
                        logStructured("otel-demo-api", sc.traceId, sc.spanId, "unauthorized")
                        ctx.respond(HttpStatusCode.Unauthorized, mapOf("error" to "unauthorized"))
                        return@post
                    }
                }
                if (rateLimitEnabled && !rateLimiter.allowRequest()) {
                    span.addEvent("rate.limit.hit")
                    logStructured("otel-demo-api", sc.traceId, sc.spanId, "rate_limited")
                    ctx.respond(HttpStatusCode.TooManyRequests, mapOf("error" to "rate_limit_exceeded"))
                    return@post
                }
                val body = runCatching { ctx.receive<ChatRequest>() }.getOrElse { e ->
                    span.recordException(e)
                    logStructured("otel-demo-api", sc.traceId, sc.spanId, "error")
                    throw e
                }

                val client = try {
                    clientFactory()
                } catch (e: Exception) {
                    span.recordException(e)
                    span.setAttribute("temporal.status", "unavailable")
                    span.setStatus(StatusCode.ERROR, "temporal_unavailable")
                    logStructured("otel-demo-api", sc.traceId, sc.spanId, "temporal_unavailable")
                    ctx.respond(
                        HttpStatusCode.ServiceUnavailable,
                        mapOf(
                            "error" to "temporal_unavailable",
                            "message" to "Temporal service is unavailable; please try again later."
                        )
                    )
                    return@post
                }

                val result = try {
                    client.runAgentWorkflowDetailed(body.message)
                } catch (e: Exception) {
                    span.recordException(e)
                    span.setAttribute("temporal.status", "unavailable")
                    span.setStatus(StatusCode.ERROR, "temporal_unavailable")
                    logStructured("otel-demo-api", sc.traceId, sc.spanId, "temporal_unavailable")
                    ctx.respond(
                        HttpStatusCode.ServiceUnavailable,
                        mapOf(
                            "error" to "temporal_unavailable",
                            "message" to "Temporal service is unavailable; please try again later."
                        )
                    )
                    return@post
                }

                span.setAttribute("workflow.id", result.workflowId)
                span.setAttribute("task.queue", result.taskQueue)
                span.setAttribute("temporal.status", "available")
                logStructured("otel-demo-api", sc.traceId, sc.spanId, "ok", result.workflowId, result.taskQueue)
                ctx.respond(ChatResponse(result.reply, result.workflowId, result.taskQueue))
            }
        } finally {
            span.end()
        }
    }
}
