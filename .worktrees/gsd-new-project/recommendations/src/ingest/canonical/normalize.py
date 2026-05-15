from __future__ import annotations

from ingest.contracts.canonical import CanonicalTrackRequest
from ingest.errors.catalog import IngestInputError
from ingest.validation.rules import ValidationContext, validate_canonical


def normalize_input(payload: dict, known_track_ids: set[str] | None = None) -> CanonicalTrackRequest:
    source_count = sum(1 for key in ("file", "url", "track_id") if key in payload and payload.get(key) is not None)
    if source_count != 1:
        raise IngestInputError("MISSING_INPUT")

    if payload.get("file") is not None:
        file_payload = payload["file"]
        if not isinstance(file_payload, dict):
            raise IngestInputError("MISSING_INPUT")

        canonical_payload = {
            "source": {"kind": "file", "reference": str(file_payload.get("name", ""))},
            "metadata": {
                "size_bytes": file_payload.get("size_bytes"),
                "extension": file_payload.get("extension"),
                "mime_type": file_payload.get("mime_type"),
            },
        }
    elif payload.get("url") is not None:
        canonical_payload = {
            "source": {"kind": "url", "reference": str(payload["url"])},
            "metadata": {"extension": _extension_from_url(str(payload["url"]))},
        }
    elif payload.get("track_id") is not None:
        canonical_payload = {
            "source": {"kind": "track_id", "reference": str(payload["track_id"])},
            "metadata": {},
        }
    else:
        raise IngestInputError("MISSING_INPUT")

    context = ValidationContext(known_track_ids=known_track_ids or set())
    return validate_canonical(canonical_payload, context=context)


def _extension_from_url(url: str) -> str | None:
    last_segment = url.rsplit("/", 1)[-1]
    if "." not in last_segment:
        return None
    extension = f".{last_segment.rsplit('.', 1)[-1]}".lower()
    return extension
