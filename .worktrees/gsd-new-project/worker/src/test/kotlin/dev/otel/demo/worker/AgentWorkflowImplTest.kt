package dev.otel.demo.worker

import dev.otel.demo.contracts.AgentWorkflow
import io.temporal.client.WorkflowOptions
import io.temporal.testing.TestWorkflowEnvironment
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test

private const val TEST_TASK_QUEUE = "test-agent-task-queue"

/**
 * Temporal TestWorkflowEnvironment-based test for AgentWorkflow.
 * Exercises the multi-step workflow (preprocess → agent → postprocess) in-memory
 * without a real Temporal cluster or Python agent.
 */
class AgentWorkflowImplTest {

    private lateinit var testEnv: TestWorkflowEnvironment

    @BeforeEach
    fun setUp() {
        testEnv = TestWorkflowEnvironment.newInstance()
        val worker = testEnv.newWorker(TEST_TASK_QUEUE)
        worker.registerWorkflowImplementationTypes(AgentWorkflowImpl::class.java)
        worker.registerActivitiesImplementations(
            PreprocessActivity(),
            object : RunAgentActivityInterface {
                override fun run(message: String): String = "mock-agent-reply"
            },
            PostprocessActivity()
        )
        testEnv.start()
    }

    @AfterEach
    fun tearDown() {
        testEnv.close()
    }

    @Test
    fun `workflow runs preprocess then agent then postprocess and returns postprocessed reply`() {
        val workflow = testEnv.workflowClient.newWorkflowStub(
            AgentWorkflow::class.java,
            WorkflowOptions.newBuilder()
                .setTaskQueue(TEST_TASK_QUEUE)
                .setWorkflowId("test-agent-1")
                .build()
        )
        val result = workflow.run("Hello")
        assertEquals("postprocessed:mock-agent-reply", result)
    }
}
