package com.k8sqarag.gitwatcher

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue

class RepoAllowlistTest {

    @Test
    fun normalizeHttps() {
        assertEquals(
            "https://github.com/octocat/hello-world",
            RepoAllowlist.normalizeGithubHttps("https://github.com/octocat/hello-world.git"),
        )
    }

    @Test
    fun normalizeGitAt() {
        assertEquals(
            "https://github.com/octocat/hello-world",
            RepoAllowlist.normalizeGithubHttps("git@github.com:octocat/hello-world.git"),
        )
    }

    @Test
    fun normalizeGitAtCaseInsensitiveHost() {
        assertEquals(
            "https://github.com/acme/widget",
            RepoAllowlist.normalizeGithubHttps("git@GitHub.com:acme/widget.git"),
        )
    }

    @Test
    fun normalizeShorthand() {
        assertEquals(
            "https://github.com/acme/cool",
            RepoAllowlist.normalizeGithubHttps("acme/cool"),
        )
    }

    @Test
    fun nonGithubReturnsNull() {
        assertNull(RepoAllowlist.normalizeGithubHttps("https://gitlab.com/a/b.git"))
    }

    @Test
    fun fileDenied() {
        assertFalse(RepoAllowlist.matches("file:///tmp/x"))
    }
}
