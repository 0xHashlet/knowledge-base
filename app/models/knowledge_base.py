from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UuidPrimaryKeyMixin


class KnowledgeBaseVisibility(str, enum.Enum):
    PRIVATE = "private"
    DEPARTMENT = "department"
    COMPANY = "company"


class KnowledgeBaseMemberRole(str, enum.Enum):
    OWNER = "owner"
    MANAGER = "manager"
    EDITOR = "editor"
    VIEWER = "viewer"


class KnowledgeBase(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_bases"

    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    visibility: Mapped[KnowledgeBaseVisibility] = mapped_column(
        Enum(KnowledgeBaseVisibility, name="knowledge_base_visibility"),
        default=KnowledgeBaseVisibility.PRIVATE,
        nullable=False,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    owner: Mapped["User"] = relationship()
    department: Mapped["Department | None"] = relationship()
    members: Mapped[list["KnowledgeBaseMember"]] = relationship(
        back_populates="knowledge_base",
        cascade="all, delete-orphan",
    )
    documents: Mapped[list["Document"]] = relationship(back_populates="knowledge_base")


class KnowledgeBaseMember(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_base_members"
    __table_args__ = (
        UniqueConstraint("knowledge_base_id", "user_id", name="uq_kb_members_kb_user"),
        Index("ix_kb_members_user_id", "user_id"),
    )

    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[KnowledgeBaseMemberRole] = mapped_column(
        Enum(KnowledgeBaseMemberRole, name="knowledge_base_member_role"),
        default=KnowledgeBaseMemberRole.VIEWER,
        nullable=False,
    )

    knowledge_base: Mapped["KnowledgeBase"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="knowledge_base_memberships")
