package dev.otel.demo.worker

import dev.otel.demo.contracts.AgentWorkflow
import io.temporal.activity.ActivityOptions
import io.temporal.common.RetryOptions
import io.temporal.workflow.Workflow
import java.time.Duration

/** Demo timeout for activity execution; visible in Temporal history and docs. */
private val AGENT_ACTIVITY_TIMEOUT = Duration.ofSeconds(60)

/** Retry policy for activities; visible in Temporal history and retry demos. */
private val AGENT_ACTIVITY_RETRY_OPTIONS = RetryOptions.newBuilder()
    .setInitialInterval(Duration.ofSeconds(3))
    .setBackoffCoefficient(2.0)
    .setMaximumAttempts(4)
    .setMaximumInterval(Duration.ofSeconds(30))
    .build()

class AgentWorkflowImpl : AgentWorkflow {
    override fun run(message: String): String {
        val options = ActivityOptions.newBuilder()
            .setScheduleToCloseTimeout(AGENT_ACTIVITY_TIMEOUT)
            .setRetryOptions(AGENT_ACTIVITY_RETRY_OPTIONS)
            .build()
        val preprocessActivity = Workflow.newActivityStub(PreprocessActivityInterface::class.java, options)
        val runAgentActivity = Workflow.newActivityStub(RunAgentActivityInterface::class.java, options)
        val postprocessActivity = Workflow.newActivityStub(PostprocessActivityInterface::class.java, options)

        val preprocessed = preprocessActivity.preprocess(message)
        val rawReply = runAgentActivity.run(preprocessed)
        return postprocessActivity.postprocess(rawReply)
    }
}
