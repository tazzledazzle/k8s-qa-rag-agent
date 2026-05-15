package com.k8sqarag.gitwatcher

import io.ktor.http.HttpStatusCode
import io.ktor.server.application.Application
import io.ktor.server.application.call
import io.ktor.server.engine.embeddedServer
import io.ktor.server.netty.Netty
import io.ktor.server.request.receiveText
import io.ktor.server.response.respond
import io.ktor.server.response.respondText
import io.ktor.server.routing.get
import io.ktor.server.routing.post
import io.ktor.server.routing.routing
import kotlinx.serialization.json.Json

fun main() {
    val port = System.getenv("PORT")?.toIntOrNull() ?: 8003
    embeddedServer(Netty, port = port, host = "0.0.0.0") { module() }.start(wait = true)
}

private val json = Json { ignoreUnknownKeys = true }

fun Application.module(
    indexTrigger: IndexTrigger = DefaultIndexTrigger,
    webhookSecretProvider: () -> String = { System.getenv("GITHUB_WEBHOOK_SECRET") ?: "" },
    repoAllowlist: (String) -> Boolean = { RepoAllowlist.matches(it) },
) {
    routing {
        get("/health") {
            call.respondText("ok")
        }
        post("/webhook") {
            val secret = webhookSecretProvider()
            val sig = call.request.headers["X-Hub-Signature-256"]
            val bodyText = call.receiveText()
            val bodyBytes = bodyText.toByteArray(Charsets.UTF_8)
            if (!GithubSignatureVerifier.verify(secret, sig, bodyBytes)) {
                call.respond(HttpStatusCode.Unauthorized, "invalid signature")
                return@post
            }
            val event = call.request.headers["X-GitHub-Event"] ?: ""
            if (event != "push") {
                call.respond(HttpStatusCode.Accepted, "ignored")
                return@post
            }
            val payload = json.decodeFromString(PushPayload.serializer(), bodyText)
            val branch = payload.ref.removePrefix("refs/heads/")
            if (!repoAllowlist(payload.repository.clone_url)) {
                call.respond(HttpStatusCode.Forbidden, "repository not allowed")
                return@post
            }
            try {
                indexTrigger.trigger(payload.repository.clone_url, branch)
            } catch (e: Exception) {
                e.printStackTrace()
            }
            call.respond(HttpStatusCode.OK, "accepted")
        }
    }
}
