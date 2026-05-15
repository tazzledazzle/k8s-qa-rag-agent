from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class TrackLookupRecord:
    track_id: str
    canonical_reference: str
    extension: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    title: str | None = None
    artist: str | None = None
    extra_metadata: dict[str, object] = field(default_factory=dict)


class TrackLookupService(Protocol):
    def get_track(self, track_id: str) -> TrackLookupRecord | None:
        """Return track metadata for a known ID, or None."""


@dataclass
class DictTrackLookupService:
    records: dict[str, TrackLookupRecord]

    def get_track(self, track_id: str) -> TrackLookupRecord | None:
        return self.records.get(track_id)
