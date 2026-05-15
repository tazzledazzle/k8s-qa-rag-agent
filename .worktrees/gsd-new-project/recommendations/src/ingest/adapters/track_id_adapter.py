from __future__ import annotations

import re

from ingest.contracts.canonical import CanonicalTrackRequest
from ingest.errors.catalog import IngestInputError
from ingest.services.track_lookup import TrackLookupService
from ingest.validation.rules import ValidationContext, validate_canonical


TRACK_ID_PATTERN = re.compile(r"^trk_[A-Za-z0-9]+$")


def normalize_track_id_input(track_id: str, *, lookup: TrackLookupService) -> CanonicalTrackRequest:
    normalized_track_id = _normalize_track_id(track_id)
    record = lookup.get_track(normalized_track_id)
    if record is None:
        raise IngestInputError("UNKNOWN_TRACK_ID")

    metadata = {
        "size_bytes": record.size_bytes,
        "extension": record.extension,
        "mime_type": record.mime_type,
        "title": record.title,
        "artist": record.artist,
    }
    metadata.update(record.extra_metadata)

    canonical_payload = {
        "source": {"kind": "track_id", "reference": record.canonical_reference},
        "metadata": metadata,
    }
    # Track IDs are resolved through lookup first and then validated through shared rules.
    context = ValidationContext(known_track_ids={record.canonical_reference})
    return validate_canonical(canonical_payload, context=context)


def _normalize_track_id(track_id: str) -> str:
    if not isinstance(track_id, str):
        raise IngestInputError("MISSING_INPUT")

    normalized = track_id.strip()
    if not normalized:
        raise IngestInputError("MISSING_INPUT")
    if not TRACK_ID_PATTERN.fullmatch(normalized):
        raise IngestInputError("INVALID_TRACK_ID")
    return normalized
