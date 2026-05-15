package dev.otel.demo.worker.client

import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.engine.cio.CIO
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.http.ContentType
import io.ktor.http.contentType
import io.ktor.serialization.jackson.jackson
import io.opentelemetry.api.GlobalOpenTelemetry
import io.opentelemetry.context.Context
import kotlinx.coroutines.runBlocking

private val client = HttpClient(CIO) {
    install(ContentNegotiation) {
        jackson()
    }
}

fun agentInvoke(baseUrl: String, message: String): String = runBlocking {
    val url = baseUrl.trimEnd('/') + "/invoke"
    val body = mapOf("message" to message)
    val carrier = mutableMapOf<String, String>()
    GlobalOpenTelemetry.get().propagators.textMapPropagator.inject(
        Context.current(),
        carrier,
        { c: MutableMap<String, String>?, k: String, v: String -> c?.set(k, v) }
    )
    val response: InvokeResponse = client.post(url) {
        contentType(ContentType.Application.Json)
        setBody(body)
        for ((key, value) in carrier) headers.append(key, value)
    }.body()
    response.reply
}

private data class InvokeResponse(val reply: String)
