# Broken observability: diagnose and fix

This doc supports the **interview scenario**: "Traces stopped showing up in Grafana." A config flag deliberately disables trace export; the candidate diagnoses and fixes it.

## Scenario

Traces no longer appear in Grafana Tempo (or only some services appear). The app still responds (e.g. `POST /chat` returns 200), but you cannot see the full trace for a request.

## How to diagnose

1. **Confirm services are running**  
   `curl -s http://localhost:8080/health` and `curl -s http://localhost:8000/health` should return OK. If not, fix the run order or ports first.

2. **Check the OTLP collector**  
   Infra must be up: `docker compose ps` (or `make infra`). The collector listens on `localhost:4317` (gRPC). If the collector is down, no traces will be stored.

3. **Check for the broken-observability flag**  
   All three services (API, Worker, Agent) respect **`OTEL_DISABLE_TRACING`**. If this env var is set to `true` or `1`, that service **does not export traces** to the collector.
   - Inspect the environment where each process is started (terminal, systemd, or Makefile). Look for `OTEL_DISABLE_TRACING=true` or `OTEL_DISABLE_TRACING=1`.
   - If any one service has it set, that service’s spans will be missing from Tempo (you may see a partial trace or no trace at all, depending on which service had tracing disabled).

4. **Check endpoint**  
   If `OTEL_EXPORTER_OTLP_ENDPOINT` is wrong (e.g. wrong host or port), traces are sent but never received. Default is `http://localhost:4317`. Ensure it matches the collector.

## How to fix

1. **Unset or turn off the flag**  
   - Unset: `unset OTEL_DISABLE_TRACING` (or remove it from the environment).
   - Or set to false: `OTEL_DISABLE_TRACING=false` (or `0`), so tracing is enabled again.

2. **Restart the affected service(s)**  
   Restart the API, Worker, and/or Agent so they pick up the new environment. If you used `make run`, stop and start again without the flag.

3. **Verify**  
   - Send a request: `curl -X POST http://localhost:8080/chat -H "Content-Type: application/json" -d '{"message":"Hello"}'`
   - In Grafana → Explore → Tempo, run TraceQL: `{ resource.service.name="otel-demo-api" }` and open the latest trace.
   - You should see spans from **otel-demo-api**, **otel-demo-worker**, and **otel-demo-agent** in one trace.

## Reference

- **Config flag:** `OTEL_DISABLE_TRACING` (see [CONFIG.md](../CONFIG.md)).
- **Trace walkthrough:** [TRACE_WALKTHROUGH.md](TRACE_WALKTHROUGH.md).
