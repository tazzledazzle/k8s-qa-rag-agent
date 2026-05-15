# External Integrations

**Analysis Date:** 2026-04-24

## APIs & External Services

**Content API:**
- JSONPlaceholder - sample posts list/detail source for shared networking
  - SDK/Client: `io.ktor:ktor-client-core` with platform engines from `shared/build.gradle.kts`
  - Auth: None detected (base URL constant in `shared/src/commonMain/kotlin/dev/speechify/kmp/network/impl/JsonPlaceholderPostsDataSource.kt`)

**Vendor SDK Boundary:**
- Speechify integration boundary - platform `expect/actual` engine contract, currently stub/simulated behavior
  - SDK/Client: local module `:speechify` (`speechify/src/commonMain/kotlin/dev/speechify/kmp/speechify/SpeechifyEngine.kt`)
  - Auth: `SPEECHIFY_API_KEY` loaded from `local.properties` in `speechify/build.gradle.kts`, consumed in `speechify/src/androidMain/kotlin/dev/speechify/kmp/speechify/SpeechifyEngine.android.kt`

## Data Storage

**Databases:**
- Local SQLite via SQLDelight
  - Connection: No external connection string; platform driver creation in `shared/src/androidMain/kotlin/dev/speechify/kmp/db/SpeechifyDatabaseFactory.android.kt` and `shared/src/desktopMain/kotlin/dev/speechify/kmp/db/SpeechifyDatabaseFactory.desktop.kt`
  - Client: generated `SpeechifyDatabase` and query APIs from schema `shared/src/commonMain/sqldelight/dev/speechify/kmp/db/Post.sq`

**File Storage:**
- Local filesystem only (desktop SQLite file and Android app database path via SQLDelight drivers)

**Caching:**
- None as separate service; local DB acts as offline cache in `shared/src/commonMain/kotlin/dev/speechify/kmp/repository/PostsRepository.kt`

## Authentication & Identity

**Auth Provider:**
- No user identity provider detected
  - Implementation: API-key style vendor credential boundary only (`SPEECHIFY_API_KEY` for Speechify Android adapter path)

## Monitoring & Observability

**Error Tracking:**
- None detected (no Sentry/Crashlytics/DataDog dependency in `gradle/libs.versions.toml`)

**Logs:**
- Basic local logging via `println` in desktop speechify stub at `speechify/src/desktopMain/kotlin/dev/speechify/kmp/speechify/SpeechifyEngine.desktop.kt`

## CI/CD & Deployment

**Hosting:**
- Not applicable for hosted backend; this repo builds client modules/apps only

**CI Pipeline:**
- GitHub Actions in `.github/workflows/ci.yml` running Android assemble, desktop tests, iOS compile, and JS tests

## Environment Configuration

**Required env vars:**
- No `.env` files detected
- Build secret/property key: `SPEECHIFY_API_KEY` (read from `local.properties` in `speechify/build.gradle.kts`)

**Secrets location:**
- `local.properties` (gitignored by `.gitignore`) for local builds
- CI secret injection path is not explicitly configured in workflow file

## Webhooks & Callbacks

**Incoming:**
- None detected

**Outgoing:**
- HTTP GET calls to JSONPlaceholder `/posts` and `/posts/{id}` in `shared/src/commonMain/kotlin/dev/speechify/kmp/network/impl/JsonPlaceholderPostsDataSource.kt`

## Dependency Boundaries

**Boundary Rules (current implementation):**
- UI app shell depends on SDK/data modules only from `composeApp/build.gradle.kts` (`:shared`, `:speechify`, `:playback-core`, `:playback-platform`, `:speechify-adapter`)
- Shared networking and persistence are isolated in `:shared`; platform HTTP engines are in `shared/src/androidMain` and `shared/src/desktopMain`
- Speechify vendor-facing API is isolated behind `expect/actual` `SpeechifyEngine` in `speechify/src/commonMain/kotlin/dev/speechify/kmp/speechify/SpeechifyEngine.kt`
- Error translation boundary from vendor layer to playback domain is isolated in `:speechify-adapter` (module dependency edges in `speechify-adapter/build.gradle.kts`)

---

*Integration audit: 2026-04-24*
