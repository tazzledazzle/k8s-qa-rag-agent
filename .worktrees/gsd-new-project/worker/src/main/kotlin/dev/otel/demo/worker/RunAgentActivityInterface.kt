package dev.otel.demo.worker

import io.temporal.activity.ActivityInterface
import io.temporal.activity.ActivityMethod

@ActivityInterface
interface RunAgentActivityInterface {
    @ActivityMethod
    fun run(message: String): String
}
