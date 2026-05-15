package com.k8sqarag.gitwatcher

import java.security.MessageDigest
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

object GithubSignatureVerifier {

    fun verify(secret: String, signature256: String?, payload: ByteArray): Boolean {
        if (secret.isEmpty() || signature256 == null) return false
        val prefix = "sha256="
        if (!signature256.startsWith(prefix)) return false
        val expectedHex = signature256.removePrefix(prefix).trim()
        val mac = Mac.getInstance("HmacSHA256")
        mac.init(SecretKeySpec(secret.toByteArray(Charsets.UTF_8), "HmacSHA256"))
        val actual = mac.doFinal(payload)
        val expected = hexToBytes(expectedHex) ?: return false
        return MessageDigest.isEqual(actual, expected)
    }

    private fun hexToBytes(hex: String): ByteArray? {
        val s = hex.lowercase().filter { it in "0123456789abcdef" }
        if (s.length % 2 != 0) return null
        return ByteArray(s.length / 2) { i ->
            ((s[i * 2].digitToInt(16) shl 4) + s[i * 2 + 1].digitToInt(16)).toByte()
        }
    }
}
