import uuid
from datetime import date
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    CheckConstraint,
    Computed,
    Date,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config import settings
from src.db.base import Base
from src.models.enums import Campus
from src.models.source import enum_values

if TYPE_CHECKING:
    from src.models.source import ApprovedSource
    from src.models.source_version import SourceVersion


class SourceChunk(Base):
    __tablename__ = "source_chunks"
    __table_args__ = (
        UniqueConstraint("source_version_id", "ordinal", name="uq_source_chunks_version_ordinal"),
        CheckConstraint("ordinal >= 0", name="ck_source_chunks_ordinal_nonnegative"),
        CheckConstraint(
            "effective_from IS NULL OR effective_to IS NULL OR effective_to >= effective_from",
            name="ck_source_chunks_effective_date_range",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("approved_sources.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    source_version_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("source_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(settings.embedding_dimension))
    search_document: Mapped[str] = mapped_column(
        TSVECTOR, Computed("to_tsvector('english', content)", persisted=True), nullable=False
    )
    heading_path: Mapped[str | None] = mapped_column(Text)
    locator: Mapped[str | None] = mapped_column(Text)
    campus: Mapped[Campus | None] = mapped_column(
        Enum(Campus, name="campus", values_callable=enum_values)
    )
    term: Mapped[str | None] = mapped_column(String(64))
    program: Mapped[str | None] = mapped_column(String(255))
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)

    source: Mapped["ApprovedSource"] = relationship(back_populates="chunks")
    source_version: Mapped["SourceVersion"] = relationship(back_populates="chunks")
