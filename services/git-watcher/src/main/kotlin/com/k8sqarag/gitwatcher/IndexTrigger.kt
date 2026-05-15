package com.k8sqarag.gitwatcher

/** Abstraction so webhook tests can assert indexer is never invoked. */
fun interface IndexTrigger {
    fun trigger(repoUrl: String, branch: String)
}

object DefaultIndexTrigger : IndexTrigger {
    override fun trigger(repoUrl: String, branch: String) {
        IndexerClient.triggerIndex(repoUrl, branch)
    }
}
