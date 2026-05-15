"""FastAPI app: POST /invoke for the Kotlin worker."""
import os
import socket
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from agent.chain import get_agent_executor
from agent.telemetry import setup_telemetry, instrument_app


def _port_available(host: str, port: int) -> bool:
    """Return True if the port can be bound (not in use)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


class InvokeRequest(BaseModel):
    message: str


class InvokeResponse(BaseModel):
    reply: str


def create_app(agent=None) -> FastAPI:
    """Create FastAPI app. Pass agent= for testing to skip real LLM."""
    otlp = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    if otlp:
        setup_telemetry("otel-demo-agent", otlp)

    auth_enabled = (os.environ.get("AGENT_AUTH_ENABLED", "") or "").strip().lower() in ("1", "true")
    expected_token = (os.environ.get("AGENT_AUTH_TOKEN") or "").strip() or None
    force_fail_all = (os.environ.get("AGENT_FAIL_ALL_REQUESTS", "") or "").strip().lower() in ("1", "true")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.agent = agent if agent is not None else get_agent_executor()
        yield
        app.state.agent = None

    app = FastAPI(title="OTel Demo Agent", lifespan=lifespan)
    instrument_app(app)

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "otel-demo-agent"}

    @app.post("/invoke", response_model=InvokeResponse)
    def invoke(request: Request, req: InvokeRequest):
        span = trace.get_current_span()
        ctx = span.get_span_context()
        raw_trace_id = getattr(ctx, "trace_id", 0) or 0
        raw_span_id = getattr(ctx, "span_id", 0) or 0
        trace_id = format(raw_trace_id, "032x") if raw_trace_id else ""
        span_id = format(raw_span_id, "016x") if raw_span_id else ""

        def log_struct(outcome: str, **extra: object) -> None:
            import json
            import sys
            payload = {
                "service": "otel-demo-agent",
                "trace_id": trace_id,
                "span_id": span_id,
                "outcome": outcome,
            }
            if extra:
                payload.update(extra)
            sys.stderr.write(json.dumps(payload) + "\n")

        span.set_attribute("message.type", "invoke")
        span.add_event("agent.invocation.start")
        log_struct("start")
        try:
            if force_fail_all:
                span.set_attribute("error.type", "agent_failure")
                span.set_attribute("agent.failure.mode", "forced_all_requests")
                span.set_status(Status(StatusCode.ERROR))
                span.add_event(
                    "agent.failure.forced",
                    {
                        "failure.mode": "forced_all_requests",
                    },
                )
                log_struct("error", error_type="agent_failure", failure_mode="forced_all_requests")
                raise HTTPException(status_code=500, detail="forced agent failure for demo")

            if auth_enabled:
                auth_header = (request.headers.get("authorization") or "").strip()
                token = auth_header
                if auth_header.lower().startswith("bearer "):
                    token = auth_header[7:].strip()
                if not expected_token or token != expected_token:
                    log_struct("unauthorized")
                    raise HTTPException(status_code=401, detail="unauthorized")

            agent_obj = app.state.agent
            result = agent_obj.invoke({"input": req.message})
            reply = result.get("output", str(result))
            span.add_event("agent.invocation.end")
            log_struct("ok")
            return InvokeResponse(reply=reply)
        except Exception as e:
            span.add_event("agent.invocation.end")
            span.record_exception(e)
            log_struct("error")
            raise

    return app


app = create_app()

if __name__ == "__main__":
    import sys
    import uvicorn
    agent_port_env = os.environ.get("AGENT_PORT")
    if agent_port_env:
        try:
            port = int(agent_port_env)
        except ValueError:
            port = 8000
    else:
        port = 8000
    host = "0.0.0.0"
    # Fail fast when using default port 8000 (whether AGENT_PORT was unset or invalid) and it's in use.
    if port == 8000 and not _port_available(host, 8000):
        sys.stderr.write(
            "Agent could not bind to port 8000. Set AGENT_PORT to a different port or stop the other process.\n"
        )
        sys.exit(1)
    uvicorn.run("agent.main:app", host=host, port=port, reload=False)
