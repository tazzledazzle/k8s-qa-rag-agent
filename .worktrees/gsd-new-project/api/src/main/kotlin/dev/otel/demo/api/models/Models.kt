package dev.otel.demo.api.models

data class ChatRequest(val message: String)

data class ChatResponse(val reply: String, val workflowId: String? = null, val taskQueue: String? = null)

data class HealthResponse(val status: String, val service: String = "otel-demo-api")

data class ReadinessResponse(
    val status: String,
    val service: String = "otel-demo-api",
    val temporal: String
)
