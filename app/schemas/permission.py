import uuid

from pydantic import Field

from app.schemas.common import ApiModel


class PermissionBase(ApiModel):
    resource: str = Field(min_length=1, max_length=80)
    action: str = Field(min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=255)


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(ApiModel):
    resource: str | None = Field(default=None, min_length=1, max_length=80)
    action: str | None = Field(default=None, min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=255)


class PermissionRead(PermissionBase):
    id: uuid.UUID

