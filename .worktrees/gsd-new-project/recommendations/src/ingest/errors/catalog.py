from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IngestErrorDefinition:
    code: str
    message: str
    stable: bool = True


INGEST_ERRORS: dict[str, IngestErrorDefinition] = {
    "MISSING_INPUT": IngestErrorDefinition(
        code="MISSING_INPUT",
        message="No ingest input was provided. Provide one of: file, url, or track_id.",
    ),
    "UNSUPPORTED_SOURCE": IngestErrorDefinition(
        code="UNSUPPORTED_SOURCE",
        message="Provided source type is not supported. Allowed sources: file, url, track_id.",
    ),
    "UNSUPPORTED_FORMAT": IngestErrorDefinition(
        code="UNSUPPORTED_FORMAT",
        message="Audio format is not supported for ingestion.",
    ),
    "INVALID_URL": IngestErrorDefinition(
        code="INVALID_URL",
        message="URL input is invalid or uses a disallowed scheme.",
    ),
    "UNKNOWN_TRACK_ID": IngestErrorDefinition(
        code="UNKNOWN_TRACK_ID",
        message="Track ID does not exist in the internal catalog.",
    ),
    "INVALID_TRACK_ID": IngestErrorDefinition(
        code="INVALID_TRACK_ID",
        message="Track ID is malformed. Expected pattern: trk_<alphanumeric>.",
    ),
    "OVERSIZED_PAYLOAD": IngestErrorDefinition(
        code="OVERSIZED_PAYLOAD",
        message="Input payload exceeds maximum allowed size.",
    ),
}


def get_error_definition(code: str) -> IngestErrorDefinition:
    return INGEST_ERRORS.get(
        code,
        IngestErrorDefinition(code="UNSUPPORTED_SOURCE", message="Input could not be normalized."),
    )


class IngestInputError(Exception):
    def __init__(self, code: str):
        self.code = code
        self.definition = get_error_definition(code)
        super().__init__(self.definition.code)

    def to_payload(self) -> dict[str, dict[str, str]]:
        return {
            "error": {
                "code": self.definition.code,
                "message": self.definition.message,
            }
        }
