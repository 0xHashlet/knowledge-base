from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UuidPrimaryKeyMixin


class FeedbackRating(str, enum.Enum):
    UP = "up"
    DOWN = "down"


class AnswerFeedback(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "answer_feedback"

    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("qa_messages.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    rating: Mapped[FeedbackRating] = mapped_column(
        Enum(FeedbackRating, name="feedback_rating"),
        nullable=False,
    )
    score: Mapped[int | None] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text)
    labels: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    message: Mapped["QaMessage"] = relationship()
    user: Mapped["User"] = relationship()
