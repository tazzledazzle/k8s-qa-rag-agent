package com.k8sqarag.gitwatcher

import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.client.statement.bodyAsText
import io.ktor.http.ContentType
import io.ktor.http.HttpStatusCode
import io.ktor.http.contentType
import io.ktor.server.testing.testApplication
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class WebhookRouteTest {

    private fun sign(secret: String, body: String): String {
        val mac = Mac.getInstance("HmacSHA256")
        mac.init(SecretKeySpec(secret.toByteArray(Charsets.UTF_8), "HmacSHA256"))
        val digest = mac.doFinal(body.toByteArray(Charsets.UTF_8))
        val hex = digest.joinToString("") { b -> "%02x".format(b) }
        return "sha256=$hex"
    }

    private val pushBody =
        """
        {"repository":{"clone_url":"https://github.com/octocat/Hello-World.git"},"ref":"refs/heads/main"}
        """.trimIndent()

    @Test
    fun `missing signature returns 401 and does not trigger index`() =
        testApplication {
            val calls = mutableListOf<Pair<String, String>>()
            application {
                module(
                    indexTrigger = IndexTrigger { u, b -> calls.add(u to b) },
                    webhookSecretProvider = { "s3cr3t" },
                    repoAllowlist = { true },
                )
            }
            val r = client.post("/webhook") {
                contentType(ContentType.Application.Json)
                setBody(pushBody)
            }
            assertEquals(HttpStatusCode.Unauthorized, r.status)
            assertTrue(calls.isEmpty())
        }

    @Test
    fun `wrong signature returns 401`() =
        testApplication {
            val calls = mutableListOf<Pair<String, String>>()
            application {
                module(
                    indexTrigger = IndexTrigger { u, b -> calls.add(u to b) },
                    webhookSecretProvider = { "s3cr3t" },
                    repoAllowlist = { true },
                )
            }
            val r =
                client.post("/webhook") {
                    contentType(ContentType.Application.Json)
                    headers.append("X-Hub-Signature-256", "sha256=" + "ab".repeat(32))
                    setBody(pushBody)
                }
            assertEquals(HttpStatusCode.Unauthorized, r.status)
            assertTrue(calls.isEmpty())
        }

    @Test
    fun `valid push triggers index once`() =
        testApplication {
            val calls = mutableListOf<Pair<String, String>>()
            val secret = "webhook-test-secret"
            application {
                module(
                    indexTrigger = IndexTrigger { u, b -> calls.add(u to b) },
                    webhookSecretProvider = { secret },
                    repoAllowlist = { true },
                )
            }
            val sig = sign(secret, pushBody)
            val r =
                client.post("/webhook") {
                    contentType(ContentType.Application.Json)
                    headers.append("X-Hub-Signature-256", sig)
                    headers.append("X-GitHub-Event", "push")
                    setBody(pushBody)
                }
            assertEquals(HttpStatusCode.OK, r.status)
            assertEquals("accepted", r.bodyAsText())
            assertEquals(1, calls.size)
            assertEquals("https://github.com/octocat/Hello-World.git", calls[0].first)
            assertEquals("main", calls[0].second)
        }

    @Test
    fun `non push returns accepted ignored`() =
        testApplication {
            val calls = mutableListOf<Pair<String, String>>()
            val secret = "x"
            application {
                module(
                    indexTrigger = IndexTrigger { u, b -> calls.add(u to b) },
                    webhookSecretProvider = { secret },
                    repoAllowlist = { true },
                )
            }
            val sig = sign(secret, pushBody)
            val r =
                client.post("/webhook") {
                    contentType(ContentType.Application.Json)
                    headers.append("X-Hub-Signature-256", sig)
                    headers.append("X-GitHub-Event", "ping")
                    setBody(pushBody)
                }
            assertEquals(HttpStatusCode.Accepted, r.status)
            assertEquals("ignored", r.bodyAsText())
            assertTrue(calls.isEmpty())
        }

    @Test
    fun `repo allowlist false returns 403`() =
        testApplication {
            val calls = mutableListOf<Pair<String, String>>()
            val secret = "s"
            application {
                module(
                    indexTrigger = IndexTrigger { u, b -> calls.add(u to b) },
                    webhookSecretProvider = { secret },
                    repoAllowlist = { false },
                )
            }
            val sig = sign(secret, pushBody)
            val r =
                client.post("/webhook") {
                    contentType(ContentType.Application.Json)
                    headers.append("X-Hub-Signature-256", sig)
                    headers.append("X-GitHub-Event", "push")
                    setBody(pushBody)
                }
            assertEquals(HttpStatusCode.Forbidden, r.status)
            assertTrue(calls.isEmpty())
        }
}
