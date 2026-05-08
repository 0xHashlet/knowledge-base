from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UuidPrimaryKeyMixin


class QaMessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class QaSession(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "qa_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    knowledge_base_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_bases.id", ondelete="SET NULL"),
    )
    title: Mapped[str | None] = mapped_column(String(255))
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)

    user: Mapped["User"] = relationship()
    knowledge_base: Mapped["KnowledgeBase | None"] = relationship()
    messages: Mapped[list["QaMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )


class QaMessage(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "qa_messages"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("qa_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[QaMessageRole] = mapped_column(
        Enum(QaMessageRole, name="qa_message_role"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    retrieval_trace: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    session: Mapped["QaSession"] = relationship(back_populates="messages")
