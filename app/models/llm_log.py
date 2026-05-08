from __future__ import annotations

import enum
import uuid
from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UuidPrimaryKeyMixin


class LlmCallType(str, enum.Enum):
    CHAT = "chat"
    EMBEDDING = "embedding"
    RERANK = "rerank"
    EVALUATION = "evaluation"


class LlmCallStatus(str, enum.Enum):
    SUCCESS = "success"
    FAILED = "failed"


class LlmCallLog(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "llm_call_logs"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    qa_message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("qa_messages.id", ondelete="SET NULL"),
    )
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    call_type: Mapped[LlmCallType] = mapped_column(
        Enum(LlmCallType, name="llm_call_type"),
        nullable=False,
    )
    status: Mapped[LlmCallStatus] = mapped_column(
        Enum(LlmCallStatus, name="llm_call_status"),
        nullable=False,
    )
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=0, nullable=False)
    request_payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    response_payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User | None"] = relationship()
    qa_message: Mapped["QaMessage | None"] = relationship()
