"""OpenAI chat wrapper."""

from __future__ import annotations

import os

from langchain_openai import ChatOpenAI  # type: ignore[import-not-found]
from pydantic import SecretStr  # type: ignore[import-not-found]


def get_chat_model() -> ChatOpenAI:
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return ChatOpenAI(model=model, temperature=0.3, api_key=SecretStr(key))
    return ChatOpenAI(model=model, temperature=0.3)
