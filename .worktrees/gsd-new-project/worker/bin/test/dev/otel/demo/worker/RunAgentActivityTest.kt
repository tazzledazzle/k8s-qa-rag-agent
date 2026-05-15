package dev.otel.demo.worker

import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.assertThrows

class RunAgentActivityTest {
    @Test
    fun `RunAgentActivity has run method`() {
        val activity = RunAgentActivity("http://localhost:8000")
        assertTrue(RunAgentActivityInterface::class.java.isInstance(activity))
    }

    @Test
    fun `RunAgentActivity propagates agent invocation errors`() {
        // Using an unreachable port to force an invocation error from the agent client.
        val activity = RunAgentActivity("http://127.0.0.1:1")

        assertThrows<Exception> {
            activity.run("hello")
        }
    }
}
