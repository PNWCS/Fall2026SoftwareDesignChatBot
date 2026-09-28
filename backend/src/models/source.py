import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Table,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.enums import SourceStatus, SourceType

if TYPE_CHECKING:
    from src.models.escalation import EscalationDestination
    from src.models.source_chunk import SourceChunk
    from src.models.source_version import SourceVersion


def enum_values(enum_type: type[StrEnum]) -> list[str]:
    return [member.value for member in enum_type]


source_escalations = Table(
    "source_escalations",
    Base.metadata,
    Column(
        "source_id",
        Uuid(as_uuid=True),
        ForeignKey("approved_sources.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "escalation_destination_id",
        Uuid(as_uuid=True),
        ForeignKey("escalation_destinations.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class ApprovedSource(Base):
    __tablename__ = "approved_sources"
    __table_args__ = (CheckConstraint("length(trim(title)) > 0", name="ck_approved_sources_title"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canonical_url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, name="source_type", values_callable=enum_values), nullable=False
    )
    owner_office: Mapped[str | None] = mapped_column(Text)
    status: Mapped[SourceStatus] = mapped_column(
        Enum(SourceStatus, name="source_status", values_callable=enum_values),
        nullable=False,
        default=SourceStatus.ACTIVE,
        server_default=SourceStatus.ACTIVE.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    versions: Mapped[list["SourceVersion"]] = relationship(back_populates="source")
    chunks: Mapped[list["SourceChunk"]] = relationship(back_populates="source")
    escalations: Mapped[list["EscalationDestination"]] = relationship(
        secondary=source_escalations, back_populates="sources"
    )
