# Architecture

**Analysis Date:** 2026-04-24

## Pattern Overview

**Overall:** Modular Kotlin Multiplatform architecture with contract-first boundaries (`expect/actual`) and platform wiring at the application edge.

**Key Characteristics:**
- Keep domain contracts in `commonMain` and isolate platform specifics in target source sets (for example `shared/src/commonMain/kotlin/dev/speechify/kmp/network/HttpClientFactory.kt` with `androidMain`/`desktopMain` actuals).
- Compose app module composes dependencies and owns lifecycle scope in entry points (`composeApp/src/androidMain/kotlin/dev/speechify/kmp/app/MainActivity.kt`, `composeApp/src/desktopMain/kotlin/dev/speechify/kmp/app/Main.kt`).
- Data access follows gateway -> store/repository -> remote/local data source -> infrastructure (`composeApp/src/commonMain/kotlin/dev/speechify/kmp/app/ui/PostsGateway.kt`, `shared/src/commonMain/kotlin/dev/speechify/kmp/store/PostStore.kt`, `shared/src/commonMain/kotlin/dev/speechify/kmp/repository/PostsRepository.kt`).

## Layers

**UI Shell Layer (`:composeApp`):**
- Purpose: Render screens, route between list/detail, and translate user actions into view-model commands.
- Location: `composeApp/src/commonMain/kotlin/dev/speechify/kmp/app/` and `composeApp/src/commonMain/kotlin/dev/speechify/kmp/app/ui/`.
- Contains: `AppRoot`, `PostsViewModel`, UI state models, `PostsGateway`.
- Depends on: `:shared`, `:speechify`, `:playback-core`, `:playback-platform`, `:speechify-adapter` (`composeApp/build.gradle.kts`).
- Used by: Android and desktop entry points in the same module.

**Shared Data Layer (`:shared`):**
- Purpose: Networking, persistence, repository orchestration, and UI-facing post store abstraction.
- Location: `shared/src/commonMain/kotlin/dev/speechify/kmp/`.
- Contains: `network/*`, `repository/*`, `db/*`, `store/PostStore.kt`.
- Depends on: Ktor, SQLDelight, coroutines (`shared/build.gradle.kts`).
- Used by: `:composeApp`.

**Playback Contracts Layer (`:playback-core`):**
- Purpose: Define playback state/events/errors and control API (`AudioSink`, `PlaybackController`).
- Location: `playback-core/src/commonMain/kotlin/dev/speechify/kmp/playback/core/PlaybackContracts.kt`.
- Contains: Sealed state/event/error models and controller orchestration logic.
- Depends on: Coroutines flow/state (`playback-core/build.gradle.kts`).
- Used by: `:playback-platform`, `:speechify-adapter`, `:composeApp`.

**Platform Playback Adapter Layer (`:playback-platform`):**
- Purpose: Provide platform-specific `AudioSink` factory behind `expect/actual`.
- Location: `playback-platform/src/commonMain/kotlin/dev/speechify/kmp/playback/platform/AudioSinkFactory.kt` plus per-target `AudioSinkFactory.*.kt`.
- Contains: `createAudioSink()` contract and target implementations.
- Depends on: `:playback-core`.
- Used by: `:composeApp`.

**Vendor Boundary Layer (`:speechify` and `:speechify-adapter`):**
- Purpose: Isolate vendor SDK surface (`SpeechifyEngine`) and map vendor failures to typed playback errors.
- Location: `speechify/src/commonMain/kotlin/dev/speechify/kmp/speechify/` and `speechify-adapter/src/commonMain/kotlin/dev/speechify/kmp/speechify/adapter/`.
- Contains: `SpeechifyEngine` expect/actual implementations, `SpeechifyPlaybackAdapter`, `mapSpeechifyError`.
- Depends on: Adapter depends on `:speechify` and `:playback-core` (`speechify-adapter/build.gradle.kts`).
- Used by: `:composeApp`.

## Data Flow

**Posts list/detail flow:**

1. UI triggers `PostsViewModel.refresh()` or `loadDetail(id)` in `composeApp/src/commonMain/kotlin/dev/speechify/kmp/app/ui/PostsViewModel.kt`.
2. `PostsViewModel` calls `PostsGateway` (`composeApp/src/commonMain/kotlin/dev/speechify/kmp/app/ui/PostsGateway.kt`).
3. `RepositoryPostsGateway.refreshPosts()` delegates to `PostStore.refreshFromNetwork()` and `post(id)` delegates to `PostsRepository.post(id)`.
4. `PostsRepository.refreshPostsAndCache()` calls remote (`PostsRemoteDataSource`) and local (`PostsLocalDataSource`) with single-writer `Mutex` and `withContext(ioDispatcher)` in `shared/src/commonMain/kotlin/dev/speechify/kmp/repository/PostsRepository.kt`.
5. SQLDelight writes/reads occur via `SqlDelightPostsLocalDataSource` (`shared/src/commonMain/kotlin/dev/speechify/kmp/db/SqlDelightPostsLocalDataSource.kt`), and UI list content updates through `PostStore.observePosts()` flow mapping.

**Playback control flow:**

1. `PlaybackController` in `playback-core/src/commonMain/kotlin/dev/speechify/kmp/playback/core/PlaybackContracts.kt` receives `load/play/pause/resume/stop`.
2. Controller delegates operations to injected `AudioSink` interface.
3. `AudioSink` is produced by `createAudioSink()` from `playback-platform` actual implementation per target.
4. Speech vendor calls run through `SpeechifyPlaybackAdapter` (`speechify-adapter/src/commonMain/kotlin/dev/speechify/kmp/speechify/adapter/SpeechifyPlaybackAdapter.kt`) to map errors into playback domain types.

**State Management:**
- UI state is `StateFlow` in `PostsViewModel`; mutable internals (`MutableStateFlow`) are private and exposed read-only.
- Persistence-driven list state is source-of-truth from SQLDelight query flow (`PostStore.observePosts()`).
- Playback state is `StateFlow<PlaybackState>` managed by `PlaybackController`.

## Key Abstractions

**Expect/Actual platform boundary:**
- Purpose: Keep common code platform-neutral and inject platform behavior at source-set edges.
- Examples: `shared/src/commonMain/kotlin/dev/speechify/kmp/network/HttpClientFactory.kt`, `speechify/src/commonMain/kotlin/dev/speechify/kmp/speechify/SpeechifyEngine.kt`, `playback-platform/src/commonMain/kotlin/dev/speechify/kmp/playback/platform/AudioSinkFactory.kt`.
- Pattern: `expect` in `commonMain`, `actual` in `androidMain`/`desktopMain`/`iosMain`/`jsMain`.

**Gateway + Repository + Store split:**
- Purpose: Separate UI mapping, persistence observation, and remote/local merge rules.
- Examples: `composeApp/src/commonMain/kotlin/dev/speechify/kmp/app/ui/PostsGateway.kt`, `shared/src/commonMain/kotlin/dev/speechify/kmp/store/PostStore.kt`, `shared/src/commonMain/kotlin/dev/speechify/kmp/repository/PostsRepository.kt`.
- Pattern: UI calls gateway; store exposes observable rows; repository owns refresh consistency and cache freshness semantics.

## Entry Points

**Android app entry:**
- Location: `composeApp/src/androidMain/kotlin/dev/speechify/kmp/app/MainActivity.kt`
- Triggers: Android activity launch.
- Responsibilities: Construct SQLDelight driver/database, create HTTP client/remote/local/repository/store, create `PostsViewModel`, and host `AppRoot`.

**Desktop app entry:**
- Location: `composeApp/src/desktopMain/kotlin/dev/speechify/kmp/app/Main.kt`
- Triggers: Desktop app `main()` startup.
- Responsibilities: Same dependency graph as Android with desktop driver and window host.

**UI root entry:**
- Location: `composeApp/src/commonMain/kotlin/dev/speechify/kmp/app/AppRoot.kt`
- Triggers: Called by platform entry points.
- Responsibilities: Build navigation graph and render list/detail screens from view-model state.

## Error Handling

**Strategy:** Convert low-level network/vendor failures into typed domain outcomes before UI/state transitions.

**Patterns:**
- Remote network layer maps HTTP/deserialize/network outcomes to sealed results (`shared/src/commonMain/kotlin/dev/speechify/kmp/network/api/PostsResults.kt`, `shared/src/commonMain/kotlin/dev/speechify/kmp/network/impl/JsonPlaceholderPostsDataSource.kt`).
- Repository maps result classes into `PostRefreshOutcome` and stale/fresh cache semantics (`shared/src/commonMain/kotlin/dev/speechify/kmp/repository/PostRefreshOutcome.kt`, `shared/src/commonMain/kotlin/dev/speechify/kmp/repository/PostsRepository.kt`).
- Speechify adapter maps thrown exceptions into `PlaybackError` (`speechify-adapter/src/commonMain/kotlin/dev/speechify/kmp/speechify/adapter/SpeechifyPlaybackAdapter.kt`).

## Cross-Cutting Concerns

**Logging:** Minimal direct logging; desktop speechify stub uses `println` in `speechify/src/desktopMain/kotlin/dev/speechify/kmp/speechify/SpeechifyEngine.desktop.kt`.
**Validation:** Input validation is local to boundary methods (for example blank text checks in `SpeechifyEngine` actuals).
**Authentication:** Speechify API key is sourced from `local.properties` into Android BuildConfig in `speechify/build.gradle.kts`; no central auth subsystem in current code.

---

*Architecture analysis: 2026-04-24*
