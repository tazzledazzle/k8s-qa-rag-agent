"""Request/response models for the QA agent API."""

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    session_id: str | None = None


class Citation(BaseModel):
    file_path: str
    start_line: int
    end_line: int


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
