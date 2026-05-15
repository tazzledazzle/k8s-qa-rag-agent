# Codebase Structure

**Analysis Date:** 2026-04-24

## Directory Layout

```text
kmp-speechify/
├── composeApp/                 # Compose Multiplatform application shell and platform entry points
├── shared/                     # Shared networking, repository, SQLDelight persistence, and store
├── playback-core/              # Playback contracts and controller state machine
├── playback-platform/          # Platform `AudioSink` factory actual implementations
├── speechify/                  # Vendor Speechify boundary (`expect/actual` engine)
├── speechify-adapter/          # Maps Speechify failures to playback-domain errors
├── docs/                       # Architecture, release notes, and implementation plans
├── gradle/                     # Version catalog (`libs.versions.toml`)
├── .github/workflows/          # CI workflow definitions
└── settings.gradle.kts         # Module registry and root project identity
```

## Directory Purposes

**`composeApp/`:**
- Purpose: Application composition root and user interface.
- Contains: `commonMain` UI/view-model/gateway plus `androidMain` and `desktopMain` bootstrapping.
- Key files: `composeApp/src/commonMain/kotlin/dev/speechify/kmp/app/AppRoot.kt`, `composeApp/src/commonMain/kotlin/dev/speechify/kmp/app/ui/PostsViewModel.kt`, `composeApp/src/androidMain/kotlin/dev/speechify/kmp/app/MainActivity.kt`, `composeApp/src/desktopMain/kotlin/dev/speechify/kmp/app/Main.kt`.

**`shared/`:**
- Purpose: Data and infrastructure layer reused by app.
- Contains: Network API/results/impl (`network`), repository contracts/logic (`repository`), SQLDelight adapter (`db`), store (`store`).
- Key files: `shared/src/commonMain/kotlin/dev/speechify/kmp/repository/PostsRepository.kt`, `shared/src/commonMain/kotlin/dev/speechify/kmp/network/impl/JsonPlaceholderPostsDataSource.kt`, `shared/src/commonMain/kotlin/dev/speechify/kmp/store/PostStore.kt`, `shared/src/commonMain/sqldelight/dev/speechify/kmp/db/Post.sq`.

**`playback-core/`:**
- Purpose: Playback domain model and control contract.
- Contains: Sealed states/events/errors and `PlaybackController`.
- Key files: `playback-core/src/commonMain/kotlin/dev/speechify/kmp/playback/core/PlaybackContracts.kt`.

**`playback-platform/`:**
- Purpose: Platform realization of `AudioSink`.
- Contains: `expect` factory in `commonMain` and `actual` implementations per target.
- Key files: `playback-platform/src/commonMain/kotlin/dev/speechify/kmp/playback/platform/AudioSinkFactory.kt`, `playback-platform/src/androidMain/kotlin/dev/speechify/kmp/playback/platform/AudioSinkFactory.android.kt`, `playback-platform/src/desktopMain/kotlin/dev/speechify/kmp/playback/platform/AudioSinkFactory.desktop.kt`.

**`speechify/`:**
- Purpose: Speechify vendor boundary module.
- Contains: `SpeechifyEngine` `expect` contract and per-platform `actual` classes.
- Key files: `speechify/src/commonMain/kotlin/dev/speechify/kmp/speechify/SpeechifyEngine.kt`, `speechify/src/androidMain/kotlin/dev/speechify/kmp/speechify/SpeechifyEngine.android.kt`, `speechify/src/desktopMain/kotlin/dev/speechify/kmp/speechify/SpeechifyEngine.desktop.kt`.

**`speechify-adapter/`:**
- Purpose: Translate vendor exceptions into playback-domain errors.
- Contains: Adapter and mapper utilities.
- Key files: `speechify-adapter/src/commonMain/kotlin/dev/speechify/kmp/speechify/adapter/SpeechifyPlaybackAdapter.kt`.

## Key File Locations

**Entry Points:**
- `composeApp/src/androidMain/kotlin/dev/speechify/kmp/app/MainActivity.kt`: Android application entry and dependency assembly.
- `composeApp/src/desktopMain/kotlin/dev/speechify/kmp/app/Main.kt`: Desktop application entry and dependency assembly.
- `composeApp/src/commonMain/kotlin/dev/speechify/kmp/app/AppRoot.kt`: Shared UI/nav root.

**Configuration:**
- `settings.gradle.kts`: Included modules and repositories.
- `build.gradle.kts`: Root plugin declarations.
- `gradle/libs.versions.toml`: Dependency and plugin versions.
- `composeApp/build.gradle.kts`, `shared/build.gradle.kts`, `playback-core/build.gradle.kts`, `playback-platform/build.gradle.kts`, `speechify/build.gradle.kts`, `speechify-adapter/build.gradle.kts`: Module build and dependency boundaries.

**Core Logic:**
- `shared/src/commonMain/kotlin/dev/speechify/kmp/repository/PostsRepository.kt`: Refresh serialization and cache freshness policy.
- `shared/src/commonMain/kotlin/dev/speechify/kmp/store/PostStore.kt`: SQLDelight flow observation and refresh delegation.
- `composeApp/src/commonMain/kotlin/dev/speechify/kmp/app/ui/PostsViewModel.kt`: UI state orchestration for list/detail.
- `playback-core/src/commonMain/kotlin/dev/speechify/kmp/playback/core/PlaybackContracts.kt`: Playback contract/state machine.

**Testing:**
- `composeApp/src/commonTest/kotlin/dev/speechify/kmp/app/ui/PostsViewModelTest.kt`
- `shared/src/commonTest/kotlin/dev/speechify/kmp/network/PostsRepositoryTest.kt`
- `shared/src/desktopTest/kotlin/dev/speechify/kmp/store/PostStoreDesktopTest.kt`
- `playback-core/src/commonTest/kotlin/dev/speechify/kmp/playback/core/PlaybackControllerTest.kt`
- `speechify-adapter/src/commonTest/kotlin/dev/speechify/kmp/speechify/adapter/SpeechifyErrorMapperTest.kt`

## Naming Conventions

**Files:**
- Kotlin source files use `PascalCase` by primary type (`PostsRepository.kt`, `SpeechifyEngine.android.kt`).
- Platform implementations append target suffix before `.kt` (`*.android.kt`, `*.desktop.kt`, `*.ios.kt`, `*.js.kt`).

**Directories:**
- Module-level directories are kebab-case (`playback-core`, `speechify-adapter`).
- Package directories are lower-case hierarchical namespaces (`dev/speechify/kmp/...`).

## Where to Add New Code

**New Feature (app-facing data/use-case):**
- Primary code: `shared/src/commonMain/kotlin/dev/speechify/kmp/` for reusable logic, then `composeApp/src/commonMain/kotlin/dev/speechify/kmp/app/ui/` for view-model/gateway integration.
- Tests: `shared/src/commonTest/kotlin/...` and `composeApp/src/commonTest/kotlin/...` for shared behavior; add target-specific tests in `desktopTest`/`androidUnitTest` only when platform behavior differs.

**New Component/Module:**
- Implementation: Add new Gradle module at repo root and include it in `settings.gradle.kts`; define dependency edges in the consuming module `build.gradle.kts`.

**Utilities:**
- Shared helpers: Keep data/network/persistence helpers in `shared/src/commonMain/kotlin/dev/speechify/kmp/`.
- Playback-related helpers: Keep in `playback-core/src/commonMain/kotlin/dev/speechify/kmp/playback/core/` or `playback-platform/src/*Main/kotlin/...` depending on whether API is common or platform-specific.

## Special Directories

**`shared/build/generated/sqldelight/`:**
- Purpose: Generated SQLDelight interfaces/implementations from `.sq` schema.
- Generated: Yes.
- Committed: No.

**`build/` (per module and root):**
- Purpose: Compiled outputs, reports, and intermediate artifacts.
- Generated: Yes.
- Committed: No.

**`.worktrees/`:**
- Purpose: Alternate checked-out worktree copies used for parallel development.
- Generated: No (created intentionally by workflow tooling).
- Committed: No.

---

*Structure analysis: 2026-04-24*
