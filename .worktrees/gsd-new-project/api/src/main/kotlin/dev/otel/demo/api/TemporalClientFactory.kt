package dev.otel.demo.api

import dev.otel.demo.contracts.AgentWorkflow
import io.temporal.client.WorkflowClient
import io.temporal.client.WorkflowClientOptions
import io.temporal.client.WorkflowOptions
import io.temporal.client.WorkflowStub
import io.temporal.serviceclient.WorkflowServiceStubs
import io.temporal.serviceclient.WorkflowServiceStubsOptions
import java.time.Duration

/** Workflow run timeout; bounds how long the overall workflow may run. */
private val WORKFLOW_RUN_TIMEOUT = Duration.ofMinutes(3)

/** Workflow task timeout; bounds how long each workflow task can be in-flight. */
private val WORKFLOW_TASK_TIMEOUT = Duration.ofSeconds(30)

object TemporalClientFactory {
    private const val TASK_QUEUE = "agent-task-queue"

    fun create(): AgentWorkflowClient {
        val endpoint = System.getenv("TEMPORAL_ADDRESS") ?: "localhost:7233"
        val service = WorkflowServiceStubs.newServiceStubs(
            WorkflowServiceStubsOptions.newBuilder().setTarget(endpoint).build()
        )
        val client = WorkflowClient.newInstance(
            service,
            WorkflowClientOptions.newBuilder().build()
        )
        return AgentWorkflowClient(client)
    }
}

object TemporalHealth {
    fun isTemporalAvailable(): Boolean {
        return try {
            val endpoint = System.getenv("TEMPORAL_ADDRESS") ?: "localhost:7233"
            val service = WorkflowServiceStubs.newServiceStubs(
                WorkflowServiceStubsOptions.newBuilder().setTarget(endpoint).build()
            )
            service.shutdown()
            true
        } catch (e: Exception) {
            false
        }
    }
}

class AgentWorkflowClient(private val client: WorkflowClient) {
    private val taskQueue = System.getenv("TEMPORAL_TASK_QUEUE") ?: "agent-task-queue"

    fun runAgentWorkflow(message: String): String {
        return runAgentWorkflowDetailed(message).reply
    }

    fun runAgentWorkflowDetailed(message: String): AgentWorkflowRunResult {
        val workflow = client.newWorkflowStub(
            AgentWorkflow::class.java,
            WorkflowOptions.newBuilder()
                .setTaskQueue(taskQueue)
                .setWorkflowId("agent-${System.currentTimeMillis()}")
                .setWorkflowRunTimeout(WORKFLOW_RUN_TIMEOUT)
                .setWorkflowTaskTimeout(WORKFLOW_TASK_TIMEOUT)
                .build()
        )
        val reply = workflow.run(message)
        val workflowId = WorkflowStub.fromTyped(workflow).execution.workflowId
        return AgentWorkflowRunResult(reply = reply, workflowId = workflowId, taskQueue = taskQueue)
    }
}

data class AgentWorkflowRunResult(val reply: String, val workflowId: String, val taskQueue: String)
