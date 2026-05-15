package dev.otel.demo.worker

/**
 * Simple deterministic post-processing for demo visibility in Temporal history and traces.
 * Wraps the agent reply so the pipeline is easy to see.
 */
class PostprocessActivity : PostprocessActivityInterface {
    override fun postprocess(reply: String): String {
        return "postprocessed:$reply"
    }
}
