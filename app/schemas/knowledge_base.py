import uuid

from pydantic import Field

from app.models.knowledge_base import KnowledgeBaseMemberRole, KnowledgeBaseVisibility
from app.schemas.common import ApiModel


class KnowledgeBaseBase(ApiModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=500)
    visibility: KnowledgeBaseVisibility = KnowledgeBaseVisibility.PRIVATE
    department_id: uuid.UUID | None = None
    is_active: bool = True


class KnowledgeBaseCreate(KnowledgeBaseBase):
    pass


class KnowledgeBaseUpdate(ApiModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=500)
    visibility: KnowledgeBaseVisibility | None = None
    department_id: uuid.UUID | None = None
    is_active: bool | None = None


class KnowledgeBaseRead(KnowledgeBaseBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class KnowledgeBaseMemberCreate(ApiModel):
    user_id: uuid.UUID
    role: KnowledgeBaseMemberRole = KnowledgeBaseMemberRole.VIEWER


class KnowledgeBaseMemberRead(ApiModel):
    id: uuid.UUID
    user_id: uuid.UUID
    username: str
    email: str
    role: KnowledgeBaseMemberRole
    knowledge_base_id: uuid.UUID

