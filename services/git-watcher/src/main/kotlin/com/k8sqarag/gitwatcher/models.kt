package com.k8sqarag.gitwatcher

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class Repo(val clone_url: String)

@Serializable
data class PushPayload(val repository: Repo, val ref: String)

@Serializable
data class IndexRequest(
    @SerialName("repo_url") val repoUrl: String,
    val branch: String = "main",
)
