import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.enums import Campus
from src.models.source import enum_values, source_escalations

if TYPE_CHECKING:
    from src.models.answer import Answer
    from src.models.source import ApprovedSource


class EscalationDestination(Base):
    __tablename__ = "escalation_destinations"
    __table_args__ = (
        CheckConstraint("length(trim(office_name)) > 0", name="ck_escalations_office_name"),
        CheckConstraint(
            "length(trim(service_description)) > 0", name="ck_escalations_service_description"
        ),
        CheckConstraint("length(trim(contact_url)) > 0", name="ck_escalations_contact_url"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    office_name: Mapped[str] = mapped_column(Text, nullable=False)
    service_description: Mapped[str] = mapped_column(Text, nullable=False)
    contact_url: Mapped[str] = mapped_column(Text, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(64))
    email: Mapped[str | None] = mapped_column(String(320))
    campus: Mapped[Campus | None] = mapped_column(
        Enum(Campus, name="campus", values_callable=enum_values)
    )
    active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    review_due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    sources: Mapped[list["ApprovedSource"]] = relationship(
        secondary=source_escalations, back_populates="escalations"
    )
    answers: Mapped[list["Answer"]] = relationship(back_populates="escalation_destination")
