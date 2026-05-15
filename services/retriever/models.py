"""Pydantic models for the retriever API."""

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    language: str | None = Field(
        default=None, description="Optional language filter hint for cache key"
    )


class ChunkHit(BaseModel):
    chunk_id: int
    score: float
    file_path: str
    language: str
    start_line: int
    end_line: int
    text: str


class SearchResponse(BaseModel):
    chunks: list[ChunkHit] = Field(default_factory=list)


class RetrieverHealthResponse(BaseModel):
    status: str
    qdrant_connected: bool
    elasticsearch_connected: bool
    redis_connected: bool
    timestamp: str
