package dev.otel.demo.worker

import io.temporal.activity.ActivityInterface
import io.temporal.activity.ActivityMethod

@ActivityInterface
interface PreprocessActivityInterface {
    @ActivityMethod
    fun preprocess(message: String): String
}
