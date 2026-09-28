"""Persistence model package and SQLAlchemy metadata registration."""

from src.db.base import Base
from src.models.answer import Answer
from src.models.citation import Citation
from src.models.enums import (
    Campus,
    ExtractionStatus,
    IngestionJobStatus,
    ResponseState,
    SourceActivationStatus,
    SourceStatus,
    SourceType,
)
from src.models.escalation import EscalationDestination
from src.models.ingestion_job import IngestionJob
from src.models.question import StudentQuestion
from src.models.source import ApprovedSource
from src.models.source_chunk import SourceChunk
from src.models.source_version import SourceVersion

__all__ = [
    "Answer",
    "ApprovedSource",
    "Base",
    "Campus",
    "Citation",
    "EscalationDestination",
    "ExtractionStatus",
    "IngestionJob",
    "IngestionJobStatus",
    "ResponseState",
    "SourceActivationStatus",
    "SourceChunk",
    "SourceStatus",
    "SourceType",
    "SourceVersion",
    "StudentQuestion",
]
