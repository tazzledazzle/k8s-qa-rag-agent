---
phase: 03-temporal
plan: 01
subsystem: api, worker, testing, docs
tags: temporal, kotlin, workflow, retry, TestWorkflowEnvironment, observability

# Dependency graph
requires:
  - phase: 02-observability
    provides: Trace propagation, API/worker spans, TRACE_WALKTHROUGH
provides:
  - Explicit workflow and activity timeouts and retry policies in code
  - Multi-step workflow (preprocess → agent → postprocess) visible in Temporal history and traces
  - Controlled failure/retry demo via "fail:" message prefix
  - ChatResponse and API logs with workflowId and taskQueue for correlation
  - Worker tests using Temporal TestWorkflowEnvironment (no real Temporal or agent)
  - docs/TEMPORAL_WALKTHROUGH.md and integration link
affects: future phases that extend workflows or add activities

# Tech tracking
tech-stack:
  added: temporal-testing (already present), PreprocessActivity/PostprocessActivity
  patterns: ActivityOptions with RetryOptions, WorkflowOptions with run/task timeouts, multi-activity chain

key-files:
  created: PreprocessActivityInterface.kt, PreprocessActivity.kt, PostprocessActivityInterface.kt, PostprocessActivity.kt, AgentWorkflowImplTest.kt, docs/TEMPORAL_WALKTHROUGH.md
  modified: AgentWorkflowImpl.kt, RunAgentActivity.kt, Main.kt, TemporalClientFactory.kt, ChatRoutes.kt, Models.kt, integration/README.md

key-decisions:
  - "AgentWorkflow contract remains run(message: String): String; no API breaking change"
  - "ChatResponse extended with optional workflowId and taskQueue for backward compatibility"
  - "Retry demo: fail: prefix and attempt < 3 trigger simulated failure; attempt >= 3 succeeds"

patterns-established:
  - "Activity timeouts and RetryOptions in workflow implementation; workflow timeouts at client"
  - "Multi-step workflow as sequential activity calls with shared ActivityOptions"

# Metrics
duration: ~15min
completed: "2026-03-03"
---

# Phase 03 Plan 01: Temporal Patterns Summary

**Explicit timeouts and retries, multi-step workflow (preprocess → agent → postprocess), controlled fail: retry demo, workflow metadata in API response, worker tests with TestWorkflowEnvironment, and TEMPORAL_WALKTHROUGH.md.**

## Performance

- **Duration:** ~15 min
- **Tasks:** 6
- **Files created:** 6; **Files modified:** 6

## Accomplishments

- **Task 1:** AgentWorkflow contract unchanged; `AgentWorkflowImpl` uses explicit `ScheduleToCloseTimeout` (60s) and `RetryOptions` (initial 3s, backoff 2.0, max 4 attempts). `TemporalClientFactory` sets `WorkflowRunTimeout` (3 min) and `WorkflowTaskTimeout` (30s); added `runAgentWorkflowDetailed` and `AgentWorkflowRunResult` for metadata.
- **Task 2:** Added `PreprocessActivity` / `PostprocessActivity` (and interfaces); `AgentWorkflowImpl` chains preprocess → runAgent → postprocess; all three activities registered in `Main.kt`. Reply is postprocessed (e.g. `postprocessed:...`).
- **Task 3:** `RunAgentActivity` triggers simulated failure when message starts with `fail:` and `attempt < 3`; span event `agent.simulated_failure`; after two failures, third attempt calls real agent and completes.
- **Task 4:** `ChatResponse(reply, workflowId?, taskQueue?)`; chat route uses `runAgentWorkflowDetailed`, responds with metadata, sets span attributes and structured log fields for workflowId and taskQueue.
- **Task 5:** `AgentWorkflowImplTest` uses `TestWorkflowEnvironment`, test task queue, stub `RunAgentActivityInterface` returning a constant; asserts multi-step result `postprocessed:mock-agent-reply`. No real Temporal or agent.
- **Task 6:** `docs/TEMPORAL_WALKTHROUGH.md` covers inspecting a workflow run, multi-step activities, retries (fail:), and stuck/long-running workflows; cross-links to TRACE_WALKTHROUGH and BROKEN_OBSERVABILITY; `integration/README.md` links to the Temporal walkthrough.

## Task Commits

1. **Task 1: Refine AgentWorkflow contract, timeouts, retry policies** — `9b50fe4` (feat)
2. **Task 2: Multi-step workflow preprocess → agent → postprocess** — `31cabd4` (feat)
3. **Task 3: Controlled failure mode (fail:)** — `da1c176` (feat)
4. **Task 4: Expose workflowId and taskQueue in API** — `0b31798` (feat)
5. **Task 5: Worker tests with Temporal TestWorkflowEnvironment** — `4669b06` (feat)
6. **Task 6: TEMPORAL_WALKTHROUGH and integration link** — `742f85c` (feat)

## Files Created/Modified

- `worker/.../PreprocessActivityInterface.kt`, `PreprocessActivity.kt` — Pre-process activity interface and implementation (trim + tag).
- `worker/.../PostprocessActivityInterface.kt`, `PostprocessActivity.kt` — Post-process activity interface and implementation (wrap reply).
- `worker/.../AgentWorkflowImpl.kt` — ActivityOptions with timeout and RetryOptions; chain of three activities.
- `worker/.../RunAgentActivity.kt` — Simulated failure for `fail:` and attempt < 3.
- `worker/.../Main.kt` — Register PreprocessActivity, RunAgentActivity, PostprocessActivity.
- `api/.../TemporalClientFactory.kt` — Workflow timeouts; `runAgentWorkflowDetailed` and `AgentWorkflowRunResult`.
- `api/.../ChatRoutes.kt` — Use `runAgentWorkflowDetailed`; respond and log workflowId/taskQueue; span attributes.
- `api/.../models/Models.kt` — `ChatResponse(reply, workflowId?, taskQueue?)`.
- `worker/.../AgentWorkflowImplTest.kt` — TestWorkflowEnvironment test for multi-step workflow.
- `docs/TEMPORAL_WALKTHROUGH.md` — Temporal-centric troubleshooting and exploration.
- `integration/README.md` — Section linking to TEMPORAL_WALKTHROUGH.

## Decisions Made

- Kept `AgentWorkflow.run(message: String): String` unchanged; all behavior is backward compatible.
- ChatResponse workflow metadata is optional (default null) so existing clients remain valid.
- Retry demo threshold: fail on attempts 1 and 2, succeed on attempt 3+ for predictable demo behavior.

## Deviations from Plan

None — plan executed as written. No auto-fixes or blocking issues.

## Verification Performed or Skipped

- **Performed:** `./gradlew :worker:test :api:test` passed after each task. AgentWorkflowImplTest validates the multi-step workflow in-memory. Contract and timeout/retry code inspected as specified.
- **Skipped (environment):** Live verification that requires the full stack (Temporal Web UI, running worker/agent, POST /chat with `fail:` and inspection in Temporal Web and Tempo) was not run in this execution environment. The plan allows skipping such checks when the environment cannot run the full stack; document in the summary. Users can follow TEMPORAL_WALKTHROUGH.md to perform these steps locally.

## Next Phase Readiness

- Phase 3 plan 01 deliverables are in place. Ready for further workflow extensions or additional observability phases.
- No blockers. Run full stack and follow TEMPORAL_WALKTHROUGH.md to confirm Temporal Web and retry behavior if desired.

## Self-Check: PASSED

- docs/TEMPORAL_WALKTHROUGH.md exists.
- .planning/phases/03-temporal/03-01-SUMMARY.md exists.
- All six task commits (9b50fe4, 31cabd4, da1c176, 0b31798, 4669b06, 742f85c) present in repo.

---
*Phase: 03-temporal*
*Completed: 2026-03-03*
