import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Integer, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.models.enums import ResponseState
from src.models.source import enum_values

if TYPE_CHECKING:
    from src.models.citation import Citation
    from src.models.escalation import EscalationDestination
    from src.models.question import StudentQuestion


class Answer(Base):
    __tablename__ = "answers"
    __table_args__ = (CheckConstraint("latency_ms >= 0", name="ck_answers_latency_nonnegative"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("student_questions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    response_state: Mapped[ResponseState] = mapped_column(
        Enum(ResponseState, name="response_state", values_callable=enum_values), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    escalation_destination_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("escalation_destinations.id", ondelete="SET NULL")
    )
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    question: Mapped["StudentQuestion"] = relationship(back_populates="answer")
    escalation_destination: Mapped["EscalationDestination | None"] = relationship(
        back_populates="answers"
    )
    citations: Mapped[list["Citation"]] = relationship(back_populates="answer")
