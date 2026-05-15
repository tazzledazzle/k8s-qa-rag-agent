package dev.otel.demo.worker

import dev.otel.demo.worker.client.agentInvoke
import io.opentelemetry.api.trace.Span
import io.opentelemetry.api.trace.StatusCode
import io.temporal.activity.Activity

private fun logStructured(service: String, traceId: String, spanId: String, outcome: String) {
    System.err.println("""{"service":"$service","trace_id":"$traceId","span_id":"$spanId","outcome":"$outcome"}""")
}

class RunAgentActivity(
    private val agentBaseUrl: String
) : RunAgentActivityInterface {
    override fun run(message: String): String {
        val span = Span.current()
        val sc = span.spanContext
        logStructured("otel-demo-worker", sc.traceId, sc.spanId, "start")
        val ctx = Activity.getExecutionContext()
        if (ctx != null) {
            val info = ctx.info
            span.setAttribute("workflow.id", info.workflowId)
            span.setAttribute("task.queue", info.activityTaskQueue)
        }
        span.addEvent("agent.invocation.start")

        // Controlled failure for retry demo: "fail:" prefix triggers failures until attempt >= 3
        if (ctx != null && message.startsWith("fail:")) {
            val attempt = ctx.info.attempt
            if (attempt < 3) {
                span.addEvent("agent.simulated_failure")
                logStructured("otel-demo-worker", sc.traceId, sc.spanId, "simulated_failure")
                throw RuntimeException("Simulated agent failure for retry demo (attempt=$attempt)")
            }
        }

        return try {
            val result = agentInvoke(agentBaseUrl, message)
            span.addEvent("agent.invocation.end")
            logStructured("otel-demo-worker", sc.traceId, sc.spanId, "ok")
            result
        } catch (e: Exception) {
            span.addEvent("agent.invocation.end")
            span.recordException(e)
            span.setAttribute("error.type", "agent_failure")
            span.setStatus(StatusCode.ERROR, "agent invocation failed")
            logStructured("otel-demo-worker", sc.traceId, sc.spanId, "error")
            throw e
        }
    }
}
