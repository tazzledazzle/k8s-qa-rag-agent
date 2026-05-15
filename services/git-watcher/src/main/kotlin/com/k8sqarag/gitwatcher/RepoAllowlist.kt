package com.k8sqarag.gitwatcher

/**
 * Matches [INDEXER_ALLOWED_GITHUB_ORGS] and [INDEXER_ALLOWED_REPO_URLS] semantics
 * documented with the Python indexer (`services/indexer/repo_allowlist.py`).
 *
 * GitHub webhooks should only deliver https://github.com/... clone URLs.
 * [file://] is always denied at the watcher (use HTTPS remotes from GitHub only).
 */
object RepoAllowlist {

    fun matches(cloneUrl: String): Boolean {
        val raw = cloneUrl.trim()
        if (raw.isEmpty()) return false
        if (raw.startsWith("file:", ignoreCase = true)) return false

        val norm = normalizeGithubHttps(raw) ?: return false

        val orgs = parseCsv(System.getenv("INDEXER_ALLOWED_GITHUB_ORGS")).map { it.lowercase() }.toSet()
        val urlEntries = parseCsv(System.getenv("INDEXER_ALLOWED_REPO_URLS"))
        val urls = urlEntries.mapNotNull { normalizeGithubHttps(it) }.toSet()
        val restrictive = orgs.isNotEmpty() || urls.isNotEmpty()
        if (!restrictive) return true

        val owner = githubOwner(norm) ?: return false
        val orgOk = orgs.isEmpty() || orgs.contains(owner)
        val urlOk = urls.isEmpty() || urls.contains(norm)
        return orgOk && urlOk
    }

    private fun parseCsv(value: String?): List<String> =
        value
            ?.split(",")
            ?.map { it.trim() }
            ?.filter { it.isNotEmpty() }
            ?: emptyList()

    fun normalizeGithubHttps(repoUrl: String): String? {
        var u = repoUrl.trim().trimEnd('/')
        if (u.endsWith(".git", ignoreCase = true)) u = u.dropLast(4)
        val lower = u.lowercase()
        if (lower.startsWith("git@github.com:")) {
            u = Regex("^git@github\\.com:", RegexOption.IGNORE_CASE).replace(u, "https://github.com/")
            u = u.trimEnd('/')
        } else if (!lower.startsWith("http") && u.contains("/") && !u.contains("://")) {
            u = "https://github.com/${u.trim('/')}"
        }
        if (!u.startsWith("https://github.com/", ignoreCase = true)) return null
        val tail = u.substring("https://github.com/".length).trim('/')
        val parts = tail.split('/').filter { it.isNotEmpty() }
        if (parts.size < 2) return null
        val owner = parts[0].lowercase()
        val repo = parts[1].lowercase().removeSuffix(".git")
        if (owner.isEmpty() || repo.isEmpty()) return null
        return "https://github.com/$owner/$repo"
    }

    private fun githubOwner(normalized: String): String? {
        val rest = normalized.removePrefix("https://github.com/").trim('/')
        return rest.split('/').firstOrNull()?.lowercase()
    }
}
