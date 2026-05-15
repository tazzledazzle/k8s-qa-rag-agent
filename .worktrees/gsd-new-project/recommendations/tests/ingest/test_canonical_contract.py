from __future__ import annotations

import pathlib
import sys


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

import pytest

from ingest.errors.catalog import INGEST_ERRORS


def test_schema_canonical_source_kind_values():
    from ingest.contracts.canonical import SourceKind

    assert SourceKind.FILE.value == "file"
    assert SourceKind.URL.value == "url"
    assert SourceKind.TRACK_ID.value == "track_id"


def test_schema_canonical_request_supports_all_phase_one_source_shapes():
    from ingest.contracts.canonical import CanonicalSourceDescriptor, CanonicalTrackRequest, SourceKind

    file_request = CanonicalTrackRequest(
        source=CanonicalSourceDescriptor(kind=SourceKind.FILE, reference="seed.mp3"),
        metadata={"size_bytes": 512},
    )
    url_request = CanonicalTrackRequest(
        source=CanonicalSourceDescriptor(kind=SourceKind.URL, reference="https://example.com/audio.wav")
    )
    id_request = CanonicalTrackRequest(
        source=CanonicalSourceDescriptor(kind=SourceKind.TRACK_ID, reference="trk_12345")
    )

    assert file_request.source.kind is SourceKind.FILE
    assert url_request.source.kind is SourceKind.URL
    assert id_request.source.kind is SourceKind.TRACK_ID


def test_error_catalog_has_stable_reason_codes_for_ingest05_rejections():
    expected_codes = {
        "MISSING_INPUT",
        "UNSUPPORTED_SOURCE",
        "UNSUPPORTED_FORMAT",
        "INVALID_URL",
        "UNKNOWN_TRACK_ID",
        "OVERSIZED_PAYLOAD",
    }

    assert set(INGEST_ERRORS) >= expected_codes


def test_error_catalog_entries_include_machine_readable_code_and_message():
    missing_input = INGEST_ERRORS["MISSING_INPUT"]

    assert missing_input.code == "MISSING_INPUT"
    assert isinstance(missing_input.message, str)
    assert missing_input.message


@pytest.mark.parametrize(
    "code",
    [
        "MISSING_INPUT",
        "UNSUPPORTED_SOURCE",
        "UNSUPPORTED_FORMAT",
        "INVALID_URL",
        "UNKNOWN_TRACK_ID",
        "OVERSIZED_PAYLOAD",
    ],
)
def test_error_catalog_entries_are_declared_stable(code: str):
    assert INGEST_ERRORS[code].stable is True


def test_validation_order_runs_shape_then_source_then_constraints_then_normalization():
    from ingest.validation.rules import ValidationContext, validate_canonical

    context = ValidationContext(known_track_ids={"trk_123"})

    validate_canonical(
        payload={
            "source": {"kind": "url", "reference": "https://example.com/audio.mp3"},
            "metadata": {"size_bytes": 512, "extension": ".mp3"},
        },
        context=context,
    )

    assert context.steps == ["shape", "source_policy", "constraints", "normalization"]


def test_constraints_reject_oversized_payload():
    from ingest.errors.catalog import IngestInputError
    from ingest.validation.rules import ValidationContext, validate_canonical

    with pytest.raises(IngestInputError) as exc_info:
        validate_canonical(
            payload={
                "source": {"kind": "file", "reference": "seed.wav"},
                "metadata": {"size_bytes": 50_000_001, "extension": ".wav"},
            },
            context=ValidationContext(),
        )

    assert exc_info.value.code == "OVERSIZED_PAYLOAD"


def test_normalize_input_returns_canonical_track_request_for_all_supported_sources():
    from ingest.canonical.normalize import normalize_input
    from ingest.contracts.canonical import SourceKind

    file_request = normalize_input({"file": {"name": "seed.mp3", "size_bytes": 1024, "extension": ".mp3"}})
    url_request = normalize_input({"url": "https://example.com/seed.wav"})
    track_id_request = normalize_input({"track_id": "trk_1"}, known_track_ids={"trk_1"})

    assert file_request.source.kind is SourceKind.FILE
    assert url_request.source.kind is SourceKind.URL
    assert track_id_request.source.kind is SourceKind.TRACK_ID


def test_normalize_input_uses_stable_error_envelope_for_invalid_paths():
    from ingest.canonical.normalize import normalize_input
    from ingest.errors.catalog import IngestInputError

    with pytest.raises(IngestInputError) as exc_info:
        normalize_input({})
    missing_input_error = exc_info.value

    with pytest.raises(IngestInputError) as exc_info:
        normalize_input({"url": "ftp://example.com/audio.mp3"})
    invalid_url_error = exc_info.value

    assert set(missing_input_error.to_payload().keys()) == {"error"}
    assert set(invalid_url_error.to_payload().keys()) == {"error"}
    assert set(missing_input_error.to_payload()["error"].keys()) == {"code", "message"}
    assert set(invalid_url_error.to_payload()["error"].keys()) == {"code", "message"}
    assert missing_input_error.to_payload()["error"]["code"] == "MISSING_INPUT"
    assert invalid_url_error.to_payload()["error"]["code"] == "INVALID_URL"
