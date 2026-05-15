package com.k8sqarag.gitwatcher

import io.ktor.client.HttpClient
import io.ktor.client.engine.cio.CIO
import io.ktor.client.plugins.HttpTimeout
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.http.ContentType
import io.ktor.http.contentType
import io.ktor.serialization.kotlinx.json.json
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.json.Json

object IndexerClient {

    private val jsonConfig = Json { ignoreUnknownKeys = true }

    fun triggerIndex(repoUrl: String, branch: String) {
        runBlocking {
            HttpClient(CIO) {
                install(ContentNegotiation) { json(jsonConfig) }
                install(HttpTimeout) {
                    requestTimeoutMillis = 10_000
                    connectTimeoutMillis = 5_000
                }
            }.use { client ->
                val host = System.getenv("INDEXER_HOST") ?: "localhost"
                val port = System.getenv("INDEXER_PORT")?.toIntOrNull() ?: 8000
                val url = "http://$host:$port/index"
                client.post(url) {
                    contentType(ContentType.Application.Json)
                    setBody(IndexRequest(repoUrl = repoUrl, branch = branch))
                }
            }
        }
    }
}
