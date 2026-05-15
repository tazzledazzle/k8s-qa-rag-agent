"""Citation extraction from LangGraph tool payloads."""

import json

from langchain_core.messages import ToolMessage

from services.qa_agent.agent import citations_from_tool_messages


def test_citations_from_tool_messages_extracts_file_paths() -> None:
    payload = {
        "chunks": [
            {
                "chunk_id": 1,
                "score": 0.9,
                "file_path": "sample_module.py",
                "language": "python",
                "start_line": 1,
                "end_line": 8,
                "text": "def phase1_verification_answer",
            }
        ]
    }
    msgs = [ToolMessage(content=json.dumps(payload), tool_call_id="call_1")]
    cits = citations_from_tool_messages(msgs)
    assert len(cits) == 1
    assert cits[0].file_path == "sample_module.py"
    assert cits[0].start_line == 1
    assert cits[0].end_line == 8


def test_citations_dedupe_same_file_span() -> None:
    chunk = {
        "chunk_id": 1,
        "score": 0.9,
        "file_path": "a.py",
        "language": "python",
        "start_line": 1,
        "end_line": 2,
        "text": "x",
    }
    body = json.dumps({"chunks": [chunk, chunk]})
    msgs = [ToolMessage(content=body, tool_call_id="c")]
    cits = citations_from_tool_messages(msgs)
    assert len(cits) == 1
