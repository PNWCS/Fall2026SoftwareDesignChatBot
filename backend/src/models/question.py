import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.models.answer import Answer


class StudentQuestion(Base):
    __tablename__ = "student_questions"
    __table_args__ = (
        CheckConstraint("length(trim(message_redacted)) > 0", name="ck_student_questions_message"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_redacted: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    answer: Mapped["Answer | None"] = relationship(back_populates="question", uselist=False)
