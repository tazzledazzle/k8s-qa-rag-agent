# Testing Patterns

**Analysis Date:** 2026-04-24

## Test Framework

**Runner:**
- Kotlin Test (`kotlin("test")` / `libs.kotlin.test`) across modules.
- Coroutines test utilities (`kotlinx-coroutines-test`) in `playback-core`, `shared`, and `composeApp`.

**Assertion Library:**
- `kotlin.test` assertions (`assertEquals`, `assertIs`, `assertTrue`, `assertFailsWith`).

**Configuration source:**
- Per-module Gradle config in:
  - `shared/build.gradle.kts`
  - `composeApp/build.gradle.kts`
  - `playback-core/build.gradle.kts`
  - `speechify-adapter/build.gradle.kts`
- No dedicated `junit-platform`, `kotest`, or coverage plugin config detected.

**Run Commands (current reality):**
```bash
./gradlew :playback-core:desktopTest :speechify-adapter:desktopTest
./gradlew :playback-core:jsTest :playback-platform:jsTest :speechify:jsTest :speechify-adapter:jsTest
./gradlew :shared:desktopTest
```

## Test File Organization

**Location pattern:**
- KMP source-set aligned:
  - `*/src/commonTest/kotlin/...`
  - `shared/src/desktopTest/kotlin/...`

**Current test files:**
- `composeApp/src/commonTest/kotlin/dev/speechify/kmp/app/ui/PostsViewModelTest.kt`
- `shared/src/commonTest/kotlin/dev/speechify/kmp/network/PostsRepositoryTest.kt`
- `shared/src/commonTest/kotlin/dev/speechify/kmp/crypto/SecureRandomBytesTest.kt`
- `shared/src/desktopTest/kotlin/dev/speechify/kmp/store/PostStoreDesktopTest.kt`
- `playback-core/src/commonTest/kotlin/dev/speechify/kmp/playback/core/PlaybackControllerTest.kt`
- `speechify-adapter/src/commonTest/kotlin/dev/speechify/kmp/speechify/adapter/SpeechifyErrorMapperTest.kt`

## Test Structure

**Patterns in code:**
- Arrange/Act/Assert style with explicit fake classes near test class.
- Coroutine tests use `runTest` and, for ViewModel tests, `UnconfinedTestDispatcher` + `advanceUntilIdle`.
- Network tests use Ktor `MockEngine` rather than live HTTP (`PostsRepositoryTest`, `PostStoreDesktopTest`).

**Mocking approach:**
- Manual fakes over mocking frameworks:
  - `FakePostsRemoteDataSource`, `FakePostsLocalDataSource`
  - `FakePostsGateway`
  - `FakeAudioSink`
- No Mockito/MockK dependency detected.

## Fixtures and Test Data

**Data strategy:**
- Inline DTO literals and inline JSON strings.
- In-memory SQLite driver for persistence integration-style tests (`JdbcSqliteDriver.IN_MEMORY`).

**Fixture location:**
- Co-located inside test files; no shared fixture/factory module.

## Coverage Reality

**Coverage tooling:**
- Not enforced: no JaCoCo/Kover config detected; no CI coverage upload step in `.github/workflows/ci.yml`.

**What is covered well:**
- Core state transitions in `PlaybackController`.
- Network result mapping and repository refresh behavior in `shared`.
- Basic UI state transitions in `PostsViewModel`.
- Error mapper behavior for adapter boundary.

**What is not covered or minimally covered:**
- `speechify` platform `actual` implementations are not directly unit tested.
- `playback-platform` `AudioSinkFactory` platform stubs have no dedicated tests.
- Compose UI composables in `AppRoot.kt` have no UI snapshot/instrumentation tests.
- Android instrumentation tests are configured in `composeApp/build.gradle.kts` but not present under `composeApp/src/androidTest`.
- iOS target is compile-validated in CI, not behavior-tested.

## Test Types in Practice

**Unit tests:**
- Primary strategy; pure logic/state and mapper coverage.

**Integration tests:**
- Limited, mostly in `shared/src/desktopTest` with real SQLDelight schema + in-memory DB and mocked network.

**E2E tests:**
- Not detected.

## CI Test Execution Reality

- CI currently runs:
  - Android assemble checks (not Android test tasks)
  - Desktop tests for only `:playback-core` and `:speechify-adapter`
  - JS tests for playback/speechify modules
  - iOS compile only
- `:shared:desktopTest` and `composeApp` common tests are not executed in CI workflow.

---

*Testing analysis: 2026-04-24*
