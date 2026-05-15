from __future__ import annotations

import pathlib
import sys

import pytest


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from ingest.adapters.track_id_adapter import normalize_track_id_input
from api.ingest.track_id_routes import ingest_track_id
from ingest.canonical.normalize import normalize_input
from ingest.errors.catalog import IngestInputError
from ingest.services.track_lookup import DictTrackLookupService, TrackLookupRecord


def _lookup_service() -> DictTrackLookupService:
    return DictTrackLookupService(
        records={
            "trk_123": TrackLookupRecord(
                track_id="trk_123",
                canonical_reference="trk_123",
                extension=".mp3",
                mime_type="audio/mpeg",
                size_bytes=4096,
                title="Neon Nights",
                artist="The Skylines",
            )
        }
    )


def test_adapter_valid_track_id_returns_canonical_request():
    request = normalize_track_id_input("trk_123", lookup=_lookup_service())

    assert request.source.kind.value == "track_id"
    assert request.source.reference == "trk_123"
    assert request.source.extension == ".mp3"
    assert request.metadata["title"] == "Neon Nights"
    assert request.metadata["artist"] == "The Skylines"


def test_adapter_unknown_track_id_raises_reason_coded_error():
    with pytest.raises(IngestInputError) as exc_info:
        normalize_track_id_input("trk_404", lookup=_lookup_service())

    assert exc_info.value.code == "UNKNOWN_TRACK_ID"


def test_adapter_malformed_track_id_raises_reason_coded_error():
    with pytest.raises(IngestInputError) as exc_info:
        normalize_track_id_input("bad-id", lookup=_lookup_service())

    assert exc_info.value.code == "INVALID_TRACK_ID"


def test_route_returns_canonical_contract_for_valid_track_id():
    response = ingest_track_id(
        payload={"track_id": "trk_123"},
        lookup=_lookup_service(),
        request_id="req_1",
    )

    assert response["request_id"] == "req_1"
    assert set(response.keys()) == {"request_id", "canonical"}
    assert response["canonical"]["source"]["kind"] == "track_id"
    assert response["canonical"]["source"]["reference"] == "trk_123"


def test_route_returns_stable_error_envelope_for_unknown_track_id():
    response = ingest_track_id(
        payload={"track_id": "trk_404"},
        lookup=_lookup_service(),
        request_id="req_2",
    )

    assert response["request_id"] == "req_2"
    assert set(response.keys()) == {"request_id", "error"}
    assert set(response["error"].keys()) == {"code", "message"}
    assert response["error"]["code"] == "UNKNOWN_TRACK_ID"


def test_track_id_canonical_shape_matches_file_and_url_contract_parity():
    track_id_response = ingest_track_id(
        payload={"track_id": "trk_123"},
        lookup=_lookup_service(),
        request_id="req_shape",
    )
    file_canonical = normalize_input({"file": {"name": "seed.mp3", "size_bytes": 1024, "extension": ".mp3"}})
    url_canonical = normalize_input({"url": "https://example.com/seed.wav"})

    track_canonical = track_id_response["canonical"]
    assert set(track_canonical.keys()) == {"source", "metadata"}
    assert set(track_canonical["source"].keys()) == {"kind", "reference", "mime_type", "extension", "size_bytes"}
    assert set(track_canonical.keys()) == set(file_canonical.__dict__.keys())
    assert set(track_canonical.keys()) == set(url_canonical.__dict__.keys())
    assert set(track_canonical["source"].keys()) == set(file_canonical.source.__dict__.keys())
    assert set(track_canonical["source"].keys()) == set(url_canonical.source.__dict__.keys())


def test_route_error_contract_is_consistent_for_malformed_track_id():
    response = ingest_track_id(
        payload={"track_id": "trk-123"},
        lookup=_lookup_service(),
        request_id="req_invalid",
    )

    assert response["request_id"] == "req_invalid"
    assert set(response.keys()) == {"request_id", "error"}
    assert set(response["error"].keys()) == {"code", "message"}
    assert response["error"]["code"] == "INVALID_TRACK_ID"
    assert isinstance(response["error"]["message"], str)
    assert response["error"]["message"]
