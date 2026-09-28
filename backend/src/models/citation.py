import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.models.answer import Answer
    from src.models.source_chunk import SourceChunk


class Citation(Base):
    __tablename__ = "citations"
    __table_args__ = (
        UniqueConstraint("answer_id", "source_chunk_id", name="uq_citations_answer_chunk"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    answer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("answers.id", ondelete="CASCADE"), nullable=False
    )
    source_chunk_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("source_chunks.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    display_title: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    locator: Mapped[str | None] = mapped_column(Text)
    review_context: Mapped[str] = mapped_column(Text, nullable=False)

    answer: Mapped["Answer"] = relationship(back_populates="citations")
    source_chunk: Mapped["SourceChunk"] = relationship()
