package dev.otel.demo.worker

import dev.otel.demo.contracts.AgentWorkflow
import io.temporal.client.WorkflowClient
import io.temporal.client.WorkflowClientOptions
import io.temporal.serviceclient.WorkflowServiceStubs
import io.temporal.serviceclient.WorkflowServiceStubsOptions
import io.temporal.worker.Worker
import io.temporal.worker.WorkerFactory
import io.temporal.worker.WorkerOptions

fun main() {
    val otelEndpoint = System.getenv("OTEL_EXPORTER_OTLP_ENDPOINT") ?: "http://localhost:4317"
    initOpenTelemetry("otel-demo-worker", otelEndpoint)

    val temporalAddress = System.getenv("TEMPORAL_ADDRESS") ?: "localhost:7233"
    val taskQueue = System.getenv("TEMPORAL_TASK_QUEUE") ?: "agent-task-queue"
    val agentBaseUrl = System.getenv("AGENT_BASE_URL") ?: "http://localhost:8000"

    try {
        val service = WorkflowServiceStubs.newServiceStubs(
            WorkflowServiceStubsOptions.newBuilder().setTarget(temporalAddress).build()
        )
        val client = WorkflowClient.newInstance(service, WorkflowClientOptions.newBuilder().build())
        val factory = WorkerFactory.newInstance(client)
        val worker = factory.newWorker(
            taskQueue,
            WorkerOptions.newBuilder().build()
        )
        worker.registerWorkflowImplementationTypes(AgentWorkflowImpl::class.java)
        worker.registerActivitiesImplementations(
            PreprocessActivity(),
            RunAgentActivity(agentBaseUrl),
            PostprocessActivity()
        )
        factory.start()
        println("Worker started; task queue=$taskQueue, agent=$agentBaseUrl")
        Thread.currentThread().join()
    } catch (e: Exception) {
        System.err.println(
            """{"service":"otel-demo-worker","event":"temporal_unavailable","message":"Failed to start worker due to Temporal connectivity","error":"${e::class.java.name}:${e.message}"}"""
        )
        e.printStackTrace()
        throw e
    }
}
