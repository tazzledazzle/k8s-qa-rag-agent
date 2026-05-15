package dev.otel.demo.contracts

import io.temporal.workflow.WorkflowInterface
import io.temporal.workflow.WorkflowMethod

@WorkflowInterface
interface AgentWorkflow {
    @WorkflowMethod
    fun run(message: String): String
}
