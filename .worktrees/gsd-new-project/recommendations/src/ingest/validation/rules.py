from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlparse

from ingest.contracts.canonical import CanonicalSourceDescriptor, CanonicalTrackRequest, SourceKind
from ingest.errors.catalog import IngestInputError


ALLOWED_AUDIO_EXTENSIONS: set[str] = {".mp3", ".wav", ".flac", ".m4a"}
ALLOWED_URL_SCHEMES: set[str] = {"https", "http"}
MAX_SOURCE_BYTES: int = 50_000_000


@dataclass
class ValidationContext:
    known_track_ids: set[str] = field(default_factory=set)
    steps: list[str] = field(default_factory=list)


def validate_canonical(payload: dict, context: ValidationContext | None = None) -> CanonicalTrackRequest:
    runtime = context or ValidationContext()

    canonical = _validate_shape(payload, runtime)
    _validate_source_policy(canonical, runtime)
    _validate_constraints(canonical, runtime)
    _validate_normalization(canonical, runtime)
    return canonical


def _validate_shape(payload: dict, context: ValidationContext) -> CanonicalTrackRequest:
    context.steps.append("shape")

    source_payload = payload.get("source")
    if not isinstance(source_payload, dict):
        raise IngestInputError("MISSING_INPUT")

    raw_kind = source_payload.get("kind")
    raw_reference = source_payload.get("reference")
    if not raw_kind or not raw_reference:
        raise IngestInputError("MISSING_INPUT")

    try:
        kind = SourceKind(str(raw_kind))
    except ValueError as error:
        raise IngestInputError("UNSUPPORTED_SOURCE") from error

    metadata = payload.get("metadata") or {}
    if not isinstance(metadata, dict):
        raise IngestInputError("MISSING_INPUT")

    descriptor = CanonicalSourceDescriptor(
        kind=kind,
        reference=str(raw_reference).strip(),
        mime_type=metadata.get("mime_type"),
        extension=metadata.get("extension"),
        size_bytes=metadata.get("size_bytes"),
    )
    return CanonicalTrackRequest(source=descriptor, metadata=metadata)


def _validate_source_policy(request: CanonicalTrackRequest, context: ValidationContext) -> None:
    context.steps.append("source_policy")
    source = request.source

    if source.kind is SourceKind.URL:
        parsed = urlparse(source.reference)
        if parsed.scheme not in ALLOWED_URL_SCHEMES or not parsed.netloc:
            raise IngestInputError("INVALID_URL")
    elif source.kind is SourceKind.TRACK_ID:
        if context.known_track_ids and source.reference not in context.known_track_ids:
            raise IngestInputError("UNKNOWN_TRACK_ID")


def _validate_constraints(request: CanonicalTrackRequest, context: ValidationContext) -> None:
    context.steps.append("constraints")
    source = request.source

    if source.size_bytes is not None and int(source.size_bytes) > MAX_SOURCE_BYTES:
        raise IngestInputError("OVERSIZED_PAYLOAD")

    extension = source.extension
    if extension:
        normalized_extension = extension.lower()
        if not normalized_extension.startswith("."):
            normalized_extension = f".{normalized_extension}"
        if normalized_extension not in ALLOWED_AUDIO_EXTENSIONS:
            raise IngestInputError("UNSUPPORTED_FORMAT")


def _validate_normalization(request: CanonicalTrackRequest, context: ValidationContext) -> None:
    context.steps.append("normalization")
    if not request.source.reference:
        raise IngestInputError("MISSING_INPUT")
