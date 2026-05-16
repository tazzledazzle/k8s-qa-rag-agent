"""LangGraph ReAct agent."""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Sequence
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage  # type: ignore[import-not-found]
from langgraph.prebuilt import create_react_agent  # type: ignore[import-not-found]

from .llm import get_chat_model
from .models import AskResponse, Citation
from .tools import search_codebase, search_runbooks

logger = logging.getLogger(__name__)

_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        model = get_chat_model()
        tools = [search_codebase, search_runbooks]
        _graph = create_react_agent(model, tools)
    return _graph


def citations_from_tool_messages(messages: Sequence[Any]) -> list[Citation]:
    """Build citation list from retriever JSON embedded in tool message bodies."""
    out: list[Citation] = []
    seen: set[tuple[str, int, int]] = set()
    for m in messages:
        if not isinstance(m, ToolMessage):
            continue
        content = m.content
        if not isinstance(content, str):
            continue
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            logger.debug("Tool message was not JSON; skip citation parse")
            continue
        chunks = data.get("chunks")
        if not isinstance(chunks, list):
            continue
        for ch in chunks:
            if not isinstance(ch, dict):
                continue
            fp = ch.get("file_path")
            if not fp:
                continue
            start = int(ch.get("start_line", 0))
            end = int(ch.get("end_line", 0))
            key = (str(fp), start, end)
            if key in seen:
                continue
            seen.add(key)
            out.append(Citation(file_path=str(fp), start_line=start, end_line=end))
    return out


def run_agent(question: str) -> AskResponse:
    graph = _get_graph()
    max_iter = int(os.getenv("AGENT_MAX_ITERATIONS", "5"))
    # recursion_limit counts internal steps; leave headroom for tool rounds
    limit = 2 + max_iter * 4
    result = graph.invoke(
        {"messages": [HumanMessage(content=question)]},
        config={"recursion_limit": limit},
    )
    messages = result.get("messages", [])
    answer_text = ""
    for m in reversed(messages):
        if isinstance(m, AIMessage) and m.content and not m.tool_calls:
            if isinstance(m.content, str):
                answer_text = m.content
            else:
                answer_text = str(m.content)
            break
    if not answer_text:
        answer_text = "No answer produced."

    citations = citations_from_tool_messages(messages)
    return AskResponse(answer=answer_text, citations=citations)
