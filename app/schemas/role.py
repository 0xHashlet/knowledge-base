import uuid

from pydantic import Field

from app.schemas.common import ApiModel


class RoleBase(ApiModel):
    name: str = Field(min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=255)


class RoleCreate(RoleBase):
    pass


class RoleUpdate(ApiModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=255)


class RoleRead(RoleBase):
    id: uuid.UUID

