import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config import settings
from src.db.base import Base
from src.models.enums import ExtractionStatus, SourceActivationStatus
from src.models.source import enum_values

if TYPE_CHECKING:
    from src.models.ingestion_job import IngestionJob
    from src.models.source import ApprovedSource
    from src.models.source_chunk import SourceChunk


class SourceVersion(Base):
    __tablename__ = "source_versions"
    __table_args__ = (
        UniqueConstraint(
            "source_id", "content_hash", name="uq_source_versions_source_content_hash"
        ),
        CheckConstraint(
            "embedding_dimension > 0", name="ck_source_versions_embedding_dimension_positive"
        ),
        CheckConstraint(
            f"embedding_dimension = {settings.embedding_dimension}",
            name="ck_source_versions_embedding_dimension_matches_config",
        ),
        Index(
            "uq_source_versions_one_active_per_source",
            "source_id",
            unique=True,
            postgresql_where=text("activation_status = 'active'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("approved_sources.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    extraction_status: Mapped[ExtractionStatus] = mapped_column(
        Enum(ExtractionStatus, name="extraction_status", values_callable=enum_values),
        nullable=False,
        default=ExtractionStatus.PENDING,
        server_default=ExtractionStatus.PENDING.value,
    )
    activation_status: Mapped[SourceActivationStatus] = mapped_column(
        Enum(SourceActivationStatus, name="source_activation_status", values_callable=enum_values),
        nullable=False,
        default=SourceActivationStatus.INACTIVE,
        server_default=SourceActivationStatus.INACTIVE.value,
    )
    embedding_model: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default=settings.embedding_model,
        server_default=settings.embedding_model,
    )
    embedding_dimension: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=settings.embedding_dimension,
        server_default=str(settings.embedding_dimension),
    )
    chunking_version: Mapped[str] = mapped_column(String(64), nullable=False)
    review_due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    source: Mapped["ApprovedSource"] = relationship(back_populates="versions")
    chunks: Mapped[list["SourceChunk"]] = relationship(back_populates="source_version")
    ingestion_jobs: Mapped[list["IngestionJob"]] = relationship(back_populates="source_version")
