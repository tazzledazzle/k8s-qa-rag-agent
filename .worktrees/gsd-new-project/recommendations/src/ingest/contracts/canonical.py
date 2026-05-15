from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SourceKind(str, Enum):
    FILE = "file"
    URL = "url"
    TRACK_ID = "track_id"


@dataclass(frozen=True)
class CanonicalSourceDescriptor:
    kind: SourceKind
    reference: str
    mime_type: str | None = None
    extension: str | None = None
    size_bytes: int | None = None


@dataclass(frozen=True)
class CanonicalTrackRequest:
    source: CanonicalSourceDescriptor
    metadata: dict[str, Any] = field(default_factory=dict)
