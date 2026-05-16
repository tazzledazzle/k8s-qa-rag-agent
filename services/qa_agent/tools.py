"""Tools that call the retriever service."""

from __future__ import annotations

import json
import os
from typing import Any, cast

import httpx
from langchain_core.tools import tool  # type: ignore[import-not-found]

from services.common.observability import CORRELATION_HEADER, correlation_id_var


def _retriever_url() -> str:
    host = os.getenv("RETRIEVER_HOST", "localhost")
    port = int(os.getenv("RETRIEVER_PORT", "8001"))
    base = os.getenv("RETRIEVER_BASE_URL")
    if base:
        return base.rstrip("/")
    return f"http://{host}:{port}"


def _search(query: str, language: str | None = None) -> dict[str, Any]:
    url = f"{_retriever_url()}/search"
    body: dict[str, Any] = {"query": query}
    if language:
        body["language"] = language
    headers: dict[str, str] = {}
    cid = correlation_id_var.get()
    if cid:
        headers[CORRELATION_HEADER] = cid
    with httpx.Client(timeout=60.0) as client:
        r = client.post(url, json=body, headers=headers or None)
        r.raise_for_status()
        return cast(dict[str, Any], r.json())


@tool
def search_codebase(query: str) -> str:
    """Search indexed source code for snippets relevant to the question."""
    data = _search(query)
    return json.dumps(data, indent=2)[:12000]


@tool
def search_runbooks(query: str) -> str:
    """Search operational runbooks and docs (same index as codebase until a runbook index exists)."""
    data = _search(query, language="markdown")
    return json.dumps(data, indent=2)[:12000]
