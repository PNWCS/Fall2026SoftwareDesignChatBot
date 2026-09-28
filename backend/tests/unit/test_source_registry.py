from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from src.models.enums import Campus, SourceStatus, SourceType
from src.models.source import ApprovedSource
from src.schemas.source_manifest import SourceManifestEntry, canonicalize_official_url
from src.services.source_registry import SourceRegistrationConflict, register_source


def manifest(**overrides: object) -> dict[str, object]:
    entry: dict[str, object] = {
        "url": "https://WWW.PNW.EDU/registrar/deadlines/?utm_source=seed#fall",
        "title": "Registration deadlines",
        "owner_office": "Office of the Registrar",
        "source_type": "policy",
        "applicability": {"campuses": ["hammond"], "terms": ["Fall 2026"]},
        "review_window_days": 90,
    }
    entry.update(overrides)
    return entry


def test_manifest_normalizes_official_url_and_scope() -> None:
    entry = SourceManifestEntry.model_validate(manifest())

    assert entry.canonical_url == "https://www.pnw.edu/registrar/deadlines"
    assert entry.applicability.campuses == [Campus.HAMMOND]
    assert entry.source_type == SourceType.POLICY


@pytest.mark.parametrize(
    "url",
    [
        "http://www.pnw.edu/policy",
        "https://pnw.edu.evil.example/policy",
        "https://user:password@www.pnw.edu/policy",
        "https://www.pnw.edu:8443/policy",
    ],
)
def test_manifest_rejects_non_official_urls(url: str) -> None:
    with pytest.raises(ValidationError):
        SourceManifestEntry.model_validate(manifest(url=url))


@pytest.mark.parametrize(
    "overrides",
    [
        {"owner_office": "  "},
        {"review_window_days": 0},
        {"applicability": {}},
        {"applicability": {"terms": 7}},
        {"owner_office": 7},
        {"source_type": "unknown"},
    ],
)
def test_manifest_requires_governance_metadata(overrides: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        SourceManifestEntry.model_validate(manifest(**overrides))


def test_url_canonicalization_sorts_query_and_removes_tracking() -> None:
    canonical = canonicalize_official_url(
        "https://www.pnw.edu/path/?z=last&utm_medium=email&a=first#section"
    )

    assert canonical == "https://www.pnw.edu/path?a=first&z=last"


def test_registration_is_idempotent_for_matching_active_source() -> None:
    entry = SourceManifestEntry.model_validate(manifest())
    existing = ApprovedSource(
        canonical_url=entry.canonical_url,
        title=entry.title,
        owner_office=entry.owner_office,
        source_type=entry.source_type,
        status=SourceStatus.ACTIVE,
    )
    session = Mock()
    session.scalar.return_value = existing

    registered = register_source(session, entry)

    assert registered is existing
    session.add.assert_not_called()
    session.flush.assert_not_called()


def test_registration_creates_and_flushes_new_source() -> None:
    entry = SourceManifestEntry.model_validate(manifest())
    session = Mock()
    session.scalar.return_value = None

    registered = register_source(session, entry)

    assert registered.canonical_url == entry.canonical_url
    assert registered.status == SourceStatus.ACTIVE
    session.add.assert_called_once_with(registered)
    session.flush.assert_called_once_with()


def test_registration_rejects_metadata_conflict() -> None:
    entry = SourceManifestEntry.model_validate(manifest())
    existing = ApprovedSource(
        canonical_url=entry.canonical_url,
        title="Different title",
        owner_office=entry.owner_office,
        source_type=entry.source_type,
        status=SourceStatus.ACTIVE,
    )
    session = Mock()
    session.scalar.return_value = existing

    with pytest.raises(SourceRegistrationConflict):
        register_source(session, entry)