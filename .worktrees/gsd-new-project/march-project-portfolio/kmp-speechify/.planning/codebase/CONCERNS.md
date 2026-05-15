# Codebase Concerns

**Analysis Date:** 2026-04-24

## Tech Debt

**Platform playback is stubbed end-to-end**
- Issue: `createAudioSink()` returns `StubAudioSink` on all platform source sets, with every operation returning `Result.success(Unit)`.
- Files: `playback-platform/src/androidMain/kotlin/dev/speechify/kmp/playback/platform/AudioSinkFactory.android.kt`, `playback-platform/src/desktopMain/kotlin/dev/speechify/kmp/playback/platform/AudioSinkFactory.desktop.kt`, `playback-platform/src/iosMain/kotlin/dev/speechify/kmp/playback/platform/AudioSinkFactory.ios.kt`, `playback-platform/src/jsMain/kotlin/dev/speechify/kmp/playback/platform/AudioSinkFactory.js.kt`
- Impact: Product behavior can report "playing" without real audio output; platform parity is unverified.
- Fix approach: Replace stubs incrementally per platform, then add behavior tests per `actual` sink contract.

**Speechify integration is mostly stubbed**
- Issue: Desktop/iOS/JS `SpeechifyEngine` return canned success paths and voice lists; Android checks key presence but still uses simulated delay and success.
- Files: `speechify/src/desktopMain/kotlin/dev/speechify/kmp/speechify/SpeechifyEngine.desktop.kt`, `speechify/src/iosMain/kotlin/dev/speechify/kmp/speechify/SpeechifyEngine.ios.kt`, `speechify/src/jsMain/kotlin/dev/speechify/kmp/speechify/SpeechifyEngine.js.kt`, `speechify/src/androidMain/kotlin/dev/speechify/kmp/speechify/SpeechifyEngine.android.kt`
- Impact: Vendor boundary contracts are present but production integration confidence is low.
- Fix approach: Introduce real SDK/HTTP adapter behind the same API and keep stubs only for explicit test/demo mode.

## Known Bugs / Behavioral Risks

**Error details are collapsed into generic messages**
- Symptoms: Network and unknown failures become broad user-facing strings (e.g., `"Network error"`, `"Offline or unreachable"`), reducing diagnosability.
- Files: `shared/src/commonMain/kotlin/dev/speechify/kmp/repository/PostsRepository.kt`, `composeApp/src/commonMain/kotlin/dev/speechify/kmp/app/ui/PostsViewModel.kt`
- Trigger: Any remote failure path during refresh/detail.
- Workaround: Inspect logs/manually reproduce; no structured telemetry path exists.

## Security Considerations

**API key exposure surface through Android BuildConfig**
- Risk: `SPEECHIFY_API_KEY` is copied into Android `BuildConfig` from `local.properties`; this is convenient but not hardened for distributable binaries.
- Files: `speechify/build.gradle.kts`, `speechify/src/androidMain/kotlin/dev/speechify/kmp/speechify/SpeechifyEngine.android.kt`
- Current mitigation: Key not committed; read from developer-local file.
- Recommendation: Gate release builds behind secure runtime token exchange or backend proxy; avoid shipping long-lived vendor keys in client config.

## Performance Bottlenecks

**Full-table rewrite on every refresh**
- Problem: `replaceAll` deletes all rows and reinserts every post, regardless of delta.
- Files: `shared/src/commonMain/kotlin/dev/speechify/kmp/db/SqlDelightPostsLocalDataSource.kt`, `shared/src/commonMain/sqldelight/dev/speechify/kmp/db/Post.sq`
- Cause: Simplicity-first persistence strategy without upsert diffing.
- Improvement path: Use keyed upserts/deletes by change set or versioning to reduce write amplification.

## Fragile Areas

**Repository/store coupling depends on freshness semantics**
- Files: `shared/src/commonMain/kotlin/dev/speechify/kmp/repository/PostsRepository.kt`, `shared/src/commonMain/kotlin/dev/speechify/kmp/store/PostStore.kt`, `composeApp/src/commonMain/kotlin/dev/speechify/kmp/app/ui/PostsViewModel.kt`
- Why fragile: UI behavior relies on subtle freshness/failure mapping and non-empty cache checks.
- Safe modification: Preserve `PostRefreshOutcome` semantics and add regression tests before changing error/freshness logic.
- Test coverage: Partial coverage exists in `PostsRepositoryTest` and `PostStoreDesktopTest`; no end-to-end UI integration test.

## Scaling Limits

**Refresh serialization is global per repository instance**
- Current capacity: One refresh operation at a time (`Mutex`) inside each `PostsRepository`.
- Limit: Concurrent refresh callers queue; throughput can degrade as feature surface grows.
- Scaling path: Keep single-writer DB guarantees but separate fetch, merge, and notification paths for larger datasets or multiple collections.

## Dependencies at Risk

**Pre-release navigation dependency**
- Risk: `androidx-navigation` is pinned to `2.8.0-alpha10`.
- Files: `gradle/libs.versions.toml`, `composeApp/build.gradle.kts`
- Impact: API/behavior may shift; upgrades can require non-trivial refactors.
- Migration plan: Move to stable navigation artifact when available and validate route serialization/back-stack behavior.

## Missing Critical Features

**No production observability pipeline**
- Problem: No structured logging, metrics, or crash reporting integration.
- Blocks: Fast diagnosis of field failures and confidence in release hardening.
- Files: No observability integration detected in module build files or runtime code; only local `println` in `speechify/src/desktopMain/.../SpeechifyEngine.desktop.kt`.

**No real CI coverage for key shared module tests**
- Problem: CI omits `:shared:desktopTest` and `composeApp` common tests.
- Blocks: Regressions in repository/store/UI state logic can merge undetected.
- Files: `.github/workflows/ci.yml`, `shared/src/commonTest/kotlin/dev/speechify/kmp/network/PostsRepositoryTest.kt`, `composeApp/src/commonTest/kotlin/dev/speechify/kmp/app/ui/PostsViewModelTest.kt`

## Test Coverage Gaps (Highest Priority)

**Platform `actual` behavior untested**
- What's not tested: Real behavior/failure modes of `SpeechifyEngine` and `AudioSinkFactory` per target.
- Files: `speechify/src/*Main/kotlin/dev/speechify/kmp/speechify/SpeechifyEngine*.kt`, `playback-platform/src/*Main/kotlin/dev/speechify/kmp/playback/platform/AudioSinkFactory*.kt`
- Risk: Cross-platform regressions ship unnoticed.
- Priority: High

**UI composables untested**
- What's not tested: Rendering and interaction behavior in `AppRoot`, `ListScreen`, `DetailScreen`.
- Files: `composeApp/src/commonMain/kotlin/dev/speechify/kmp/app/AppRoot.kt`
- Risk: Navigation and state rendering regressions are not caught automatically.
- Priority: High

---

*Concerns audit: 2026-04-24*
# Codebase Concerns

**Analysis Date:** 2026-04-24

## Tech Debt

**Playback platform adapters are all no-op stubs:**
- Issue: Every platform `createAudioSink()` returns a `StubAudioSink` where `load/play/pause/resume/stop/seekTo/setRate/setVoice` all return `Result.success(Unit)` and never perform audio IO.
- Files: `playback-platform/src/androidMain/kotlin/dev/speechify/kmp/playback/platform/AudioSinkFactory.android.kt`, `playback-platform/src/iosMain/kotlin/dev/speechify/kmp/playback/platform/AudioSinkFactory.ios.kt`, `playback-platform/src/desktopMain/kotlin/dev/speechify/kmp/playback/platform/AudioSinkFactory.desktop.kt`, `playback-platform/src/jsMain/kotlin/dev/speechify/kmp/playback/platform/AudioSinkFactory.js.kt`
- Impact: Integration paths can appear healthy in UI and tests while real playback is absent; deployment risk is high because failures are not exercised.
- Fix approach: Replace stubs with real platform sinks behind the same `AudioSink` contract; keep a dedicated fake implementation only in test source sets.

**Speechify implementations are mostly stubs and diverge by platform:**
- Issue: Android checks `BuildConfig.SPEECHIFY_API_KEY`, but iOS/JS return synthetic success with fixed voices; desktop logs and succeeds without vendor calls.
- Files: `speechify/src/androidMain/kotlin/dev/speechify/kmp/speechify/SpeechifyEngine.android.kt`, `speechify/src/iosMain/kotlin/dev/speechify/kmp/speechify/SpeechifyEngine.ios.kt`, `speechify/src/jsMain/kotlin/dev/speechify/kmp/speechify/SpeechifyEngine.js.kt`, `speechify/src/desktopMain/kotlin/dev/speechify/kmp/speechify/SpeechifyEngine.desktop.kt`
- Impact: Cross-platform behavior is non-equivalent; adapter and controller code cannot be trusted to behave consistently once real SDK wiring begins.
- Fix approach: Define a shared error/feature capability contract and enforce parity tests per platform (unsupported platforms should return explicit typed failures, not synthetic success).

## Known Bugs

**Desktop app database initialization fails on second launch:**
- Symptoms: Desktop startup attempts schema creation every run against persistent file `jdbc:sqlite:kmp_speechify_desktop.db`; schema SQL includes plain `CREATE TABLE post (...)` without `IF NOT EXISTS`.
- Files: `composeApp/src/desktopMain/kotlin/dev/speechify/kmp/app/Main.kt`, `shared/src/commonMain/sqldelight/dev/speechify/kmp/db/Post.sq`, `shared/src/commonMain/kotlin/dev/speechify/kmp/db/SpeechifyDatabaseFactory.kt`
- Trigger: Run desktop app once to create DB, close, then run again with existing DB file.
- Workaround: Delete `kmp_speechify_desktop.db` before relaunching (data loss).

## Security Considerations

**Speechify API key is compiled into Android BuildConfig:**
- Risk: `SPEECHIFY_API_KEY` from `local.properties` is embedded via `buildConfigField`, making extraction from app artifacts feasible.
- Files: `speechify/build.gradle.kts`, `speechify/src/androidMain/kotlin/dev/speechify/kmp/speechify/SpeechifyEngine.android.kt`
- Current mitigation: Key is excluded from VCS by sourcing `local.properties`.
- Recommendations: Move vendor calls behind a backend token broker or use short-lived session tokens; avoid shipping long-lived secrets in client binaries.

## Performance Bottlenecks

**Refresh path rewrites entire posts table every successful sync:**
- Problem: `replaceAll()` performs `deleteAll()` then re-inserts all rows inside one transaction for every successful remote fetch.
- Files: `shared/src/commonMain/kotlin/dev/speechify/kmp/db/SqlDelightPostsLocalDataSource.kt`, `shared/src/commonMain/kotlin/dev/speechify/kmp/repository/PostsRepository.kt`
- Cause: Full-replace strategy with no diffing or incremental update.
- Improvement path: Add upsert-by-id diffing and stale-row pruning; retain full-replace only for explicit hard refreshes.

## Fragile Areas

**PlaybackController state machine allows invalid transitions and swallows failures:**
- Files: `playback-core/src/commonMain/kotlin/dev/speechify/kmp/playback/core/PlaybackContracts.kt`
- Why fragile: `play()` can be called before successful `load()` (uses default empty `loadedText`), and `pause/resume/stop` ignore `onFailure`, leaving stale state with no error signal.
- Safe modification: Introduce explicit transition guards (`Idle -> Loading -> Playing` etc.) and set `PlaybackState.Error` on all command failures.
- Test coverage: Current tests only assert success path with always-success sink in `playback-core/src/commonTest/kotlin/dev/speechify/kmp/playback/core/PlaybackControllerTest.kt`.

## Scaling Limits

**Network refresh throughput is single-writer serialized and non-batched:**
- Current capacity: One refresh at a time due to `Mutex` in repository; each refresh re-fetches full list and rewrites full local table.
- Limit: Frequent refresh triggers (manual retries/background sync) queue behind mutex and amplify IO/network load.
- Files: `shared/src/commonMain/kotlin/dev/speechify/kmp/repository/PostsRepository.kt`, `shared/src/commonMain/kotlin/dev/speechify/kmp/db/SqlDelightPostsLocalDataSource.kt`
- Scaling path: Add refresh coalescing/debouncing, ETag/If-Modified-Since support, and incremental local updates.

## Dependencies at Risk

**Placeholder data provider used as runtime dependency:**
- Risk: App logic depends on `https://jsonplaceholder.typicode.com` default base URL in production code path.
- Impact: Demo endpoint instability/rate limiting/outages directly surface as user-facing failures.
- Files: `shared/src/commonMain/kotlin/dev/speechify/kmp/network/impl/JsonPlaceholderPostsDataSource.kt`, `composeApp/src/androidMain/kotlin/dev/speechify/kmp/app/MainActivity.kt`, `composeApp/src/desktopMain/kotlin/dev/speechify/kmp/app/Main.kt`
- Migration plan: Inject environment-specific base URL and wrap provider behind an internal API contract before production release.

## Missing Critical Features

**No migration path for evolving SQLDelight schema:**
- Problem: Repository documents v1-only schema expectations; persistent DB creation path has no migration orchestration.
- Blocks: Safe rollout of schema changes on installed desktop/android clients.
- Files: `README.md`, `shared/src/commonMain/sqldelight/dev/speechify/kmp/db/Post.sq`, `composeApp/src/desktopMain/kotlin/dev/speechify/kmp/app/Main.kt`

**No lifecycle-managed disposal for network/database resources in app dependencies:**
- Problem: `AppDependencies.close()` cancels only coroutine scope; `HttpClient` and SQL drivers are not explicitly closed.
- Blocks: Long-running stability and predictable resource usage in desktop/mobile sessions.
- Files: `composeApp/src/commonMain/kotlin/dev/speechify/kmp/app/AppDependencies.kt`, `composeApp/src/androidMain/kotlin/dev/speechify/kmp/app/MainActivity.kt`, `composeApp/src/desktopMain/kotlin/dev/speechify/kmp/app/Main.kt`

## Test Coverage Gaps

**Failure-path coverage is missing where behavior is currently fragile:**
- What's not tested: Playback command failures (`pause/resume/stop`), invalid transition attempts, and event stream behavior (`events` remains unused in controller logic).
- Files: `playback-core/src/commonMain/kotlin/dev/speechify/kmp/playback/core/PlaybackContracts.kt`, `playback-core/src/commonTest/kotlin/dev/speechify/kmp/playback/core/PlaybackControllerTest.kt`
- Risk: Regressions in error propagation and playback state consistency can ship undetected.
- Priority: High

**CI does not execute shared data-layer tests on desktop lane:**
- What's not tested: `:shared:desktopTest` (contains repository and store tests) is not part of `check-desktop`.
- Files: `.github/workflows/ci.yml`, `shared/src/commonTest/kotlin/dev/speechify/kmp/network/PostsRepositoryTest.kt`, `shared/src/desktopTest/kotlin/dev/speechify/kmp/store/PostStoreDesktopTest.kt`
- Risk: Data-layer regressions may pass CI despite broken networking/persistence behavior.
- Priority: High

---

*Concerns audit: 2026-04-24*
