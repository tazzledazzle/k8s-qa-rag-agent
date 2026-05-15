package dev.otel.demo.worker

/**
 * Simple deterministic pre-processing for demo visibility in Temporal history and traces.
 * Trims whitespace and tags the message so the pipeline is easy to see.
 */
class PreprocessActivity : PreprocessActivityInterface {
    override fun preprocess(message: String): String {
        val trimmed = message.trim()
        return if (trimmed.isEmpty()) "preprocessed:(empty)" else "preprocessed:$trimmed"
    }
}
