from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UuidPrimaryKeyMixin


class Department(UuidPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "departments"
    __table_args__ = (UniqueConstraint("parent_id", "name", name="uq_departments_parent_name"),)

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[str | None] = mapped_column(String(64), unique=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
    )

    parent: Mapped[Department | None] = relationship(remote_side="Department.id")
    users: Mapped[list["User"]] = relationship(back_populates="department")
