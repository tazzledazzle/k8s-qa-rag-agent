# Temporal-centric debugging walkthrough

Use **Temporal Web UI** and **Grafana Tempo** to inspect workflow runs, multi-step activity chains, retries, and long-running or stuck workflows. This doc complements [TRACE_WALKTHROUGH.md](TRACE_WALKTHROUGH.md) (trace-first debugging).

## Prerequisites

- Infrastructure and all three apps running (e.g. `make run` or follow [integration/README.md](../integration/README.md)).
- At least one successful `POST /chat` so a workflow execution exists (e.g. `curl -X POST http://localhost:8080/chat -H "Content-Type: application/json" -d '{"message":"Hello"}'`).
- Optional: Temporal Web UI (e.g. from [Temporal CLI](https://docs.temporal.io/cli) or a separate `temporal-ui` setup) to view workflow history. If you only have the server on `localhost:7233`, you can use the API response `workflowId` and `taskQueue` to correlate with traces in Grafana.

---

## 1. Inspect a simple workflow run

- **Temporal Web UI:** If you have Temporal Web running, open it and filter by **Workflow Type** `AgentWorkflow` (or search by workflow ID). Each run shows:
  - **Input:** the `message` argument to `AgentWorkflow.run(message)`.
  - **Output:** the final string returned (post-processed reply).
  - **Task queue:** `agent-task-queue` (or the value of `TEMPORAL_TASK_QUEUE`).
- **Correlate with the API:** The `POST /chat` response includes `workflowId` and `taskQueue`. Use that `workflowId` in Temporal Web to open the same run, or in Grafana Tempo to find the trace (e.g. by attribute `workflow.id`).
- **Code:** The workflow contract is in `contracts/AgentWorkflow.kt` (`run(message: String): String`). The client sets workflow timeouts in `api/TemporalClientFactory.kt` (`WORKFLOW_RUN_TIMEOUT`, `WORKFLOW_TASK_TIMEOUT`).

---

## 2. See multi-step workflows

Each chat request is executed by a single workflow that runs **three activities in sequence**:

1. **Preprocess** — trims and tags the message (e.g. `preprocessed:Hello`).
2. **Run agent** — calls the Python agent and returns its reply.
3. **Postprocess** — wraps the reply (e.g. `postprocessed:<reply>`).

- **In Temporal Web:** Open a workflow execution and look at the **History**. You should see three activity tasks in order: `PreprocessActivity`, `RunAgentActivity`, and `PostprocessActivity`. Their inputs and outputs match the pipeline above.
- **In Tempo:** Open the trace for that request. The worker spans (and any activity spans) should show the sequence of work; you can use span names or attributes to see the multi-step flow.
- **Code:** The chain is implemented in `worker/AgentWorkflowImpl.kt`: same `ActivityOptions` (timeout and retry policy) are used for all three activities; see `AGENT_ACTIVITY_TIMEOUT` and `AGENT_ACTIVITY_RETRY_OPTIONS` there.

---

## 3. Observe retries and failures

A **controlled failure** mode demonstrates Temporal retries without affecting normal traffic.

- **How to trigger:** Send a message that starts with the prefix `fail:`:
  ```bash
  curl -X POST http://localhost:8080/chat -H "Content-Type: application/json" -d '{"message":"fail:Hello"}'
  ```
- **Behavior:** The `RunAgentActivity` implementation (in `worker/RunAgentActivity.kt`) checks the message and the current **attempt** from `Activity.getExecutionContext().info.attempt`. If the message starts with `fail:` and the attempt is less than 3, the activity throws a simulated failure. After two failed attempts, the third attempt (and any further retries) calls the real agent and completes. The workflow eventually succeeds; the retries are visible in history and traces.
- **In Temporal Web:** Open the workflow run for that request. The **RunAgentActivity** activity should show **multiple attempts** (e.g. Attempt 1, 2, then 3). Each failed attempt appears in the history with the failure reason; the final attempt succeeds.
- **In Tempo:** Open the trace for the same request. You should see multiple activity-related spans or events (e.g. error events or `agent.simulated_failure` span event) before the final successful activity completion.
- **Code:** Retry behavior is configured in `worker/AgentWorkflowImpl.kt` via `AGENT_ACTIVITY_RETRY_OPTIONS` (initial interval ~3s, backoff coefficient 2.0, maximum attempts 4). The simulated failure is in `worker/RunAgentActivity.kt` (prefix `fail:` and `attempt < 3`).

---

## 4. Identify stuck or long-running workflows

- **Workflow run timeout:** The client limits how long a workflow may run (see `WORKFLOW_RUN_TIMEOUT` in `api/TemporalClientFactory.kt`, default 3 minutes). If the workflow does not complete within that time, the run is terminated.
- **Activity timeout:** Each activity is bounded by `AGENT_ACTIVITY_TIMEOUT` in `worker/AgentWorkflowImpl.kt` (e.g. 60 seconds schedule-to-close). If an activity exceeds that, Temporal will retry according to `AGENT_ACTIVITY_RETRY_OPTIONS`.
- **In Temporal Web:** Filter or list workflows by status (e.g. **Running**). Long-running or stuck runs will stay in Running until they complete, time out, or are terminated. Compare the workflow start time and the current time to see how long a run has been active.
- **In Tempo:** Use the trace timeline to see where time is spent (e.g. long activity span for the agent call). The `workflow.id` and `task.queue` attributes on spans help correlate with a specific workflow execution in Temporal.

---

## See also

- [TRACE_WALKTHROUGH.md](TRACE_WALKTHROUGH.md) — TraceQL and trace-driven debugging across API, worker, and agent.
- [BROKEN_OBSERVABILITY.md](BROKEN_OBSERVABILITY.md) — What to do when traces or observability stop showing up (e.g. `OTEL_DISABLE_TRACING`).
- [CONFIG.md](../CONFIG.md) — Environment variables and ports (Temporal address, task queue, etc.).
