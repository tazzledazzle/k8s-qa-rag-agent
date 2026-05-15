# Plan 02-01 summary — Git watcher + SEC-03 (webhook path)

**Executed:** 2026-05-15  
**Requirements:** SEC-01, SEC-03 (webhook / trigger path)

## Decisions

- **Dependency injection in Ktor:** `Application.module` accepts `IndexTrigger`, `webhookSecretProvider`, and `repoAllowlist` for tests and future overrides; production defaults preserve real behavior.
- **Allowlist parity:** Kotlin `RepoAllowlist` mirrors indexer CSV env semantics; `file://` is always denied at the watcher. `git@` host matching is case-insensitive (aligned with Python `repo_allowlist`).

## Delivered

- `IndexTrigger` + `DefaultIndexTrigger`; `RepoAllowlist` with `matches` / `normalizeGithubHttps`.
- `GitWatcherApp.kt` — signature verification → push-only → allowlist → trigger; **403** when clone URL is not allowed.
- Unit tests: `GithubSignatureVerifierTest`, `RepoAllowlistTest`, `WebhookRouteTest` (Ktor `testApplication`).
- `build.gradle.kts` — JUnit 5 + Ktor server tests.

## Verification

- `gradle test --no-daemon` in `services/git-watcher/` (system Gradle when no wrapper).
