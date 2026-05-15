# Technology Stack

**Analysis Date:** 2026-04-24

## Languages

**Primary:**
- Kotlin 2.0.21 - Multiplatform app and libraries in `composeApp/src`, `shared/src`, `playback-core/src`, `playback-platform/src`, `speechify/src`, `speechify-adapter/src`

**Secondary:**
- SQL (SQLDelight `.sq`) - local schema in `shared/src/commonMain/sqldelight/dev/speechify/kmp/db/Post.sq`
- YAML - CI pipeline in `.github/workflows/ci.yml`

## Runtime

**Environment:**
- JVM 17 (Android and desktop targets) configured in `composeApp/build.gradle.kts`, `shared/build.gradle.kts`, `playback-core/build.gradle.kts`, `playback-platform/build.gradle.kts`, `speechify/build.gradle.kts`, `speechify-adapter/build.gradle.kts`
- Android API 26-35 configured in module `android {}` blocks and versions in `gradle/libs.versions.toml`
- iOS and JS runtime targets declared in `playback-core/build.gradle.kts`, `playback-platform/build.gradle.kts`, `speechify/build.gradle.kts`, `speechify-adapter/build.gradle.kts`

**Package Manager:**
- Gradle Wrapper 8.14.3 via `gradle/wrapper/gradle-wrapper.properties`
- Lockfile: Version catalog present in `gradle/libs.versions.toml` (no npm/yarn/pnpm lockfile detected)

## Frameworks

**Core:**
- Kotlin Multiplatform plugin (`org.jetbrains.kotlin.multiplatform`) - cross-platform modules declared in root `build.gradle.kts`
- Compose Multiplatform 1.7.1 + Compose compiler plugin - UI shell in `composeApp/build.gradle.kts`
- Ktor Client 3.0.2 - networking in `shared/src/commonMain/kotlin/dev/speechify/kmp/network/impl/JsonPlaceholderPostsDataSource.kt`
- kotlinx.serialization 1.7.3 - DTO and JSON decode in `shared/src/commonMain/kotlin/dev/speechify/kmp/network/dto/PostDto.kt`
- SQLDelight 2.0.2 - persistence layer in `shared/build.gradle.kts` and `shared/src/commonMain/kotlin/dev/speechify/kmp/db/SpeechifyDatabaseFactory.kt`

**Testing:**
- Kotlin test (`kotlin("test")`) across modules in each module `build.gradle.kts`
- kotlinx-coroutines-test in `playback-core/build.gradle.kts`, `playback-platform/build.gradle.kts`, `shared/build.gradle.kts`, `composeApp/build.gradle.kts`
- Ktor MockEngine for network tests in `shared/src/commonTest/kotlin/dev/speechify/kmp/network/PostsRepositoryTest.kt`

**Build/Dev:**
- Android Gradle Plugin 8.7.2 in `gradle/libs.versions.toml`
- GitHub Actions CI matrix in `.github/workflows/ci.yml`

## Key Dependencies

**Critical:**
- `org.jetbrains.kotlin:kotlin-stdlib`/KMP plugins (version catalog `kotlin = 2.0.21`) - enables shared source sets and `expect/actual` boundaries
- `io.ktor:ktor-client-core` + platform engines (`ktor-client-android`, `ktor-client-cio`) - typed HTTP client boundary in `shared/src/commonMain/kotlin/dev/speechify/kmp/network/HttpClientFactory.kt`
- `app.cash.sqldelight:runtime` + drivers (`android-driver`, `sqlite-driver`) - shared local data storage from `shared/src/commonMain/kotlin/dev/speechify/kmp/repository/PostsRepository.kt`

**Infrastructure:**
- `org.jetbrains.compose` and Material3/runtime/foundation packages - app shell and navigation in `composeApp/src/commonMain/kotlin/dev/speechify/kmp/app/AppRoot.kt`
- `org.jetbrains.androidx.navigation:navigation-compose` - shared navigation graph in `composeApp/src/commonMain/kotlin/dev/speechify/kmp/app/AppRoot.kt`
- `org.jetbrains.kotlinx:kotlinx-coroutines-core` - async orchestration in `shared/src/commonMain/kotlin/dev/speechify/kmp/store/PostStore.kt`

## Configuration

**Environment:**
- Android Speechify key is sourced from `local.properties` as `SPEECHIFY_API_KEY` and compiled to `BuildConfig` in `speechify/build.gradle.kts`
- `local.properties` is gitignored in `.gitignore`

**Build:**
- Multi-module declarations and repository setup in `settings.gradle.kts`
- Root plugin/version catalog wiring in `build.gradle.kts` and `gradle/libs.versions.toml`
- Global Gradle/KMP flags in `gradle.properties`

## Platform Requirements

**Development:**
- JDK 17 required by module compiler options and CI in `.github/workflows/ci.yml`
- Android SDK required for `:composeApp:assembleDebug` (documented in `README.md`)
- Node.js 20 required for JS checks in `.github/workflows/ci.yml`

**Production:**
- Android app packaging target via `:composeApp` in `composeApp/build.gradle.kts`
- Desktop JVM app packaging via Compose desktop in `composeApp/build.gradle.kts`
- iOS and JS targets currently compile/test at module level; app distribution path is not defined in repository config

---

*Stack analysis: 2026-04-24*
