from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UuidPrimaryKeyMixin


class DocumentStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class DocumentVersionStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    PARSED = "parsed"
    EMBEDDING = "embedding"
    READY = "ready"
    FAILED = "failed"


class Document(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("knowledge_base_id", "external_id", name="uq_documents_kb_external_id"),
    )

    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), default="upload", nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status"),
        default=DocumentStatus.ACTIVE,
        nullable=False,
    )
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    knowledge_base: Mapped["KnowledgeBase"] = relationship(back_populates="documents")
    versions: Mapped[list["DocumentVersion"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        foreign_keys="DocumentVersion.document_id",
    )


class DocumentVersion(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_versions"
    __table_args__ = (
        UniqueConstraint("document_id", "version_number", name="uq_document_versions_number"),
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    parser_name: Mapped[str | None] = mapped_column(String(80))
    parser_version: Mapped[str | None] = mapped_column(String(40))
    status: Mapped[DocumentVersionStatus] = mapped_column(
        Enum(DocumentVersionStatus, name="document_version_status"),
        default=DocumentVersionStatus.UPLOADED,
        nullable=False,
    )
    raw_text: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    is_latest: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    document: Mapped["Document"] = relationship(
        back_populates="versions",
        foreign_keys=[document_id],
    )
    knowledge_base: Mapped["KnowledgeBase"] = relationship()
    uploaded_by: Mapped["User"] = relationship()
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document_version",
        cascade="all, delete-orphan",
    )
