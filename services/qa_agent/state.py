"""Agent state (documented contract; LangGraph uses message list in practice)."""

from typing import TypedDict


class AgentStateDict(TypedDict, total=False):
    question: str
    answer: str
    iterations: int
    answer_complete: bool
