package dev.otel.demo.worker

import io.temporal.activity.ActivityInterface
import io.temporal.activity.ActivityMethod

@ActivityInterface
interface PostprocessActivityInterface {
    @ActivityMethod
    fun postprocess(reply: String): String
}
