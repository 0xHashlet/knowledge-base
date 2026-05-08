import uuid

from pydantic import Field

from app.schemas.common import ApiModel


class DepartmentBase(ApiModel):
    name: str = Field(min_length=1, max_length=128)
    code: str | None = Field(default=None, max_length=64)
    parent_id: uuid.UUID | None = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(ApiModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    code: str | None = Field(default=None, max_length=64)
    parent_id: uuid.UUID | None = None


class DepartmentRead(DepartmentBase):
    id: uuid.UUID

