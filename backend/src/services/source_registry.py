from collections.abc import Mapping
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.enums import SourceStatus
from src.models.source import ApprovedSource
from src.schemas.source_manifest import SourceManifestEntry, canonicalize_official_url


class SourceRegistrationConflict(ValueError):
    """Raised when a canonical URL is already registered with different metadata."""


def validate_source_manifest(
    manifest: SourceManifestEntry | Mapping[str, Any],
) -> SourceManifestEntry:
    if isinstance(manifest, SourceManifestEntry):
        return manifest
    return SourceManifestEntry.model_validate(manifest)


def register_source(
    session: Session,
    manifest: SourceManifestEntry | Mapping[str, Any],
) -> ApprovedSource:
    entry = validate_source_manifest(manifest)
    canonical_url = canonicalize_official_url(entry.url)
    existing = session.scalar(
        select(ApprovedSource).where(ApprovedSource.canonical_url == canonical_url)
    )

    if existing is not None:
        metadata_matches = (
            existing.title == entry.title
            and existing.owner_office == entry.owner_office
            and existing.source_type == entry.source_type
        )
        if not metadata_matches or existing.status != SourceStatus.ACTIVE:
            raise SourceRegistrationConflict(
                "canonical source URL is registered with conflicting or inactive metadata: "
                f"{canonical_url}"
            )
        return existing

    source = ApprovedSource(
        canonical_url=canonical_url,
        title=entry.title,
        owner_office=entry.owner_office,
        source_type=entry.source_type,
        status=SourceStatus.ACTIVE,
    )
    session.add(source)
    session.flush()
    return source