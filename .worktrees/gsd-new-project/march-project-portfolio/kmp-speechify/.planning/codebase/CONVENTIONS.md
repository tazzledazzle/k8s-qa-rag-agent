# Coding Conventions

**Analysis Date:** 2026-04-24

## Naming Patterns

**Files:**
- Use PascalCase for Kotlin files named after primary type/composable, e.g. `shared/src/commonMain/kotlin/dev/speechify/kmp/repository/PostsRepository.kt`, `composeApp/src/commonMain/kotlin/dev/speechify/kmp/app/AppRoot.kt`.
- Use platform suffixes for `expect/actual` files, e.g. `SpeechifyEngine.android.kt`, `AudioSinkFactory.ios.kt`, `HttpClientFactory.desktop.kt`.

**Functions:**
- Use lowerCamelCase for methods and top-level functions, e.g. `refreshPostsAndCache`, `mapSpeechifyError`, `createPlatformHttpClient`.
- Test names are readable sentence-style camelCase or backtick names in UI tests, e.g. `refreshOnNetworkErrorFailsWhenLocalEmpty`, ``refresh failure with empty cache shows error``.

**Variables/Parameters:**
- LowerCamelCase for locals/params (`ioDispatcher`, `refreshMutex`, `baseUrl`), with explicit immutable `val` default.

**Types:**
- Use PascalCase for classes/interfaces and sealed hierarchies (`PostsListResult`, `PlaybackState`, `PostRefreshOutcome`).
- Use `data object` / `data class` in sealed interfaces for state and result modeling in `playback-core` and UI state models.

## Code Style

**Formatting:**
- Trailing commas are consistently used in multiline parameter lists and constructors (example: `PostsRepository`, `PostsViewModel`).
- Explicit access and type declarations are favored at public boundaries (`StateFlow<PostsUiState>`, `Result<Unit>`).

**Linting:**
- Not detected: no `detekt`, `ktlint`, or explicit style config file in repo root (`.editorconfig`, `detekt.yml`, `ktlint` config not present).
- Style consistency is currently convention-driven rather than tool-enforced.

## Import Organization

**Order:**
1. Project imports (`dev.speechify...`)
2. Third-party libraries (`io.ktor...`, `kotlinx.coroutines...`)
3. Kotlin test imports in test files (`kotlin.test...`)

**Path Aliases:**
- Not applicable; package-based imports are used directly.

## Error Handling

**Patterns:**
- Map external/network errors into sealed result types instead of throwing (`PostsListResult`, `PostDetailResult`) in `shared/src/commonMain/kotlin/dev/speechify/kmp/network/impl/JsonPlaceholderPostsDataSource.kt`.
- Preserve cancellation by rethrowing `CancellationException`.
- Use `Result<T>` for speech/playback boundaries (`speechify` and `playback-core`) and adapt errors via explicit mapper in `speechify-adapter`.

## Logging

**Framework:** `println` only (minimal stub logging).

**Patterns:**
- Logging exists only in stubbed desktop Speechify implementation (`speechify/src/desktopMain/.../SpeechifyEngine.desktop.kt`).
- No centralized logging abstraction in current modules.

## Comments

**When to Comment:**
- Comments document architectural intent and phase constraints (repository/store/network files in `shared/src/commonMain`).
- Inline comments are rare and used for intent disambiguation in tests (`SecureRandomBytesTest`).

**KDoc usage:**
- KDoc present at key boundaries and adapters; utility/simple methods typically skip docs.

## Function Design

**Size:**
- Functions are generally small to medium and single-purpose (mapping, refresh, platform wrappers).

**Parameters:**
- Dependency injection through constructors with defaults for platform/test flexibility (`ioDispatcher` default in `PostsRepository`).

**Return Values:**
- Prefer typed outcomes (`sealed interface`, `Result`) over nullable primitives for domain/API boundaries.

## Module/Packaging Design

**Exports and boundaries:**
- Package structure follows feature/layer boundaries: `network.dto`, `network.api`, `network.impl`, `repository`, `store`.
- Cross-platform boundaries use `expect/actual` in dedicated modules (`speechify`, `playback-platform`, `shared` network factory).

**Barrel files:**
- Not used; modules import concrete package symbols directly.

---

*Convention analysis: 2026-04-24*
