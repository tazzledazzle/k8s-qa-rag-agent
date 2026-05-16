"""FastAPI entrypoint for the QA agent."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException  # type: ignore[import-not-found]
from pydantic import BaseModel  # type: ignore[import-not-found]

from services.common.observability import CorrelationIdMiddleware, create_app_lifespan

from .agent import run_agent
from .models import AskRequest, AskResponse

logger = logging.getLogger(__name__)

app = FastAPI(title="QA Agent", lifespan=create_app_lifespan("qa-agent"))
app.add_middleware(CorrelationIdMiddleware, service="qa-agent")


class HealthResponse(BaseModel):
    status: str
    timestamp: str


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", timestamp=datetime.now(timezone.utc).isoformat())


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    try:
        return run_agent(req.question)
    except Exception as e:
        logger.exception("Agent failed")
        raise HTTPException(status_code=502, detail=str(e)) from e
