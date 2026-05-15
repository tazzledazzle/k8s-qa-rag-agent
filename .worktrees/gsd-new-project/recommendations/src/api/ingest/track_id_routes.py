from __future__ import annotations

from dataclasses import asdict
from uuid import uuid4

from ingest.adapters.track_id_adapter import normalize_track_id_input
from ingest.errors.catalog import IngestInputError
from ingest.services.track_lookup import TrackLookupService


def ingest_track_id(
    *,
    payload: dict,
    lookup: TrackLookupService,
    request_id: str | None = None,
) -> dict:
    current_request_id = request_id or f"req_{uuid4().hex[:12]}"
    track_id = payload.get("track_id") if isinstance(payload, dict) else None

    try:
        canonical = normalize_track_id_input(track_id, lookup=lookup)
    except IngestInputError as error:
        response = error.to_payload()
        response["request_id"] = current_request_id
        return {"request_id": current_request_id, "error": response["error"]}

    return {
        "request_id": current_request_id,
        "canonical": asdict(canonical),
    }
