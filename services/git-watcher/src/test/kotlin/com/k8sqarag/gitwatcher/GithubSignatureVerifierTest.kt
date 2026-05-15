package com.k8sqarag.gitwatcher

import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec
import kotlin.test.Test
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class GithubSignatureVerifierTest {

    @Test
    fun `empty secret rejects`() {
        val body = "payload".toByteArray()
        assertFalse(GithubSignatureVerifier.verify("", "sha256=ab", body))
    }

    @Test
    fun `null header rejects`() {
        assertFalse(GithubSignatureVerifier.verify("secret", null, "x".toByteArray()))
    }

    @Test
    fun `wrong prefix rejects`() {
        assertFalse(GithubSignatureVerifier.verify("secret", "md5=beef", "x".toByteArray()))
    }

    @Test
    fun `odd hex rejects`() {
        assertFalse(GithubSignatureVerifier.verify("secret", "sha256=abc", "x".toByteArray()))
    }

    @Test
    fun `wrong mac rejects`() {
        val body = "hello".toByteArray()
        assertFalse(GithubSignatureVerifier.verify("secret", "sha256" + "=" + "00".repeat(32), body))
    }

    @Test
    fun `correct mac accepts`() {
        val secret = "my-secret"
        val body = """{"repository":{"clone_url":"https://github.com/o/r.git"},"ref":"refs/heads/main"}"""
        val mac = Mac.getInstance("HmacSHA256")
        mac.init(SecretKeySpec(secret.toByteArray(Charsets.UTF_8), "HmacSHA256"))
        val digest = mac.doFinal(body.toByteArray(Charsets.UTF_8))
        val hex = digest.joinToString("") { b -> "%02x".format(b) }
        assertTrue(GithubSignatureVerifier.verify(secret, "sha256=$hex", body.toByteArray(Charsets.UTF_8)))
    }

    @Test
    fun `wrong secret rejects valid shape`() {
        val body = "x".toByteArray()
        val mac = Mac.getInstance("HmacSHA256")
        mac.init(SecretKeySpec("a".toByteArray(Charsets.UTF_8), "HmacSHA256"))
        val hex = mac.doFinal(body).joinToString("") { b -> "%02x".format(b) }
        assertFalse(GithubSignatureVerifier.verify("b", "sha256=$hex", body))
    }
}
