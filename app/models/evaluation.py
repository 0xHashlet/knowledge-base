from __future__ import annotations

import enum
import uuid
from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UuidPrimaryKeyMixin


class EvaluationRunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class EvaluationDataset(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "evaluation_datasets"

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    knowledge_base: Mapped["KnowledgeBase"] = relationship()
    created_by: Mapped["User"] = relationship()
    cases: Mapped[list["EvaluationCase"]] = relationship(
        back_populates="dataset",
        cascade="all, delete-orphan",
    )


class EvaluationCase(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "evaluation_cases"

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evaluation_datasets.id", ondelete="CASCADE"),
        nullable=False,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    expected_answer: Mapped[str | None] = mapped_column(Text)
    expected_citations: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)

    dataset: Mapped["EvaluationDataset"] = relationship(back_populates="cases")


class EvaluationRun(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "evaluation_runs"

    dataset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evaluation_datasets.id", ondelete="CASCADE"),
        nullable=False,
    )
    triggered_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[EvaluationRunStatus] = mapped_column(
        Enum(EvaluationRunStatus, name="evaluation_run_status"),
        default=EvaluationRunStatus.PENDING,
        nullable=False,
    )
    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    summary: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)

    dataset: Mapped["EvaluationDataset"] = relationship()
    triggered_by: Mapped["User"] = relationship()
    results: Mapped[list["EvaluationResult"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
    )


class EvaluationResult(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "evaluation_results"

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evaluation_cases.id", ondelete="CASCADE"),
        nullable=False,
    )
    answer: Mapped[str | None] = mapped_column(Text)
    citations: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    metrics: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=0, nullable=False)

    run: Mapped["EvaluationRun"] = relationship(back_populates="results")
    case: Mapped["EvaluationCase"] = relationship()
