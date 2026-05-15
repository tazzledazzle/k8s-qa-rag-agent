"""Pydantic schemas for Indexer service."""

from typing import Optional
from pydantic import BaseModel, Field


class IndexRequest(BaseModel):
    """Request to index a repository."""

    repo_url: str = Field(
        ...,
        description="GitHub repository URL, or file:///absolute/path to a local git checkout",
    )
    branch: str = Field(default="main", description="Git branch to index")
    include_patterns: Optional[list[str]] = Field(
        default=None, description="Glob patterns for files to include"
    )
    exclude_patterns: Optional[list[str]] = Field(
        default=None, description="Glob patterns for files to exclude"
    )


class ChunkMetadata(BaseModel):
    """Metadata for a code chunk."""

    file_path: str
    language: str
    start_line: int
    end_line: int
    chunk_text: str
    deterministic_id: int


class IndexResponse(BaseModel):
    """Response from indexing."""

    status: str
    chunks_indexed: int
    total_files: int
    duration_seconds: float
    repo_url: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    qdrant_connected: bool
    elasticsearch_connected: bool
    timestamp: str
