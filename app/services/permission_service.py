import uuid
from collections.abc import Iterable

from app.models.knowledge_base import (
    KnowledgeBaseMemberRole,
    KnowledgeBaseVisibility,
)
from app.models.user import User
from app.repositories.permission_repository import PermissionRepository


class PermissionService:
    def __init__(self, repository: PermissionRepository):
        self.repository = repository

    def has_permission(self, user: User, resource: str, action: str) -> bool:
        if user.is_superuser:
            return True
        direct_permissions = {
            f"{permission.resource}:{permission.action}"
            for role in user.roles
            for permission in role.permissions
        }
        repository_permissions = self.repository.get_user_permissions(user.id)
        return f"{resource}:{action}" in direct_permissions | repository_permissions

    def can_access_knowledge_base(self, user: User, knowledge_base_id: uuid.UUID) -> bool:
        if user.is_superuser:
            return True
        knowledge_base = self.repository.get_knowledge_base(knowledge_base_id)
        if knowledge_base is None or knowledge_base.is_active is False:
            return False
        if knowledge_base.owner_id == user.id:
            return True
        if knowledge_base.visibility == KnowledgeBaseVisibility.COMPANY:
            return True
        if (
            knowledge_base.visibility == KnowledgeBaseVisibility.DEPARTMENT
            and knowledge_base.department_id is not None
            and knowledge_base.department_id == user.department_id
        ):
            return True
        return self.repository.user_has_kb_membership(user.id, knowledge_base_id)

    def can_manage_knowledge_base(self, user: User, knowledge_base_id: uuid.UUID) -> bool:
        if user.is_superuser:
            return True
        knowledge_base = self.repository.get_knowledge_base(knowledge_base_id)
        if knowledge_base is None:
            return False
        if knowledge_base.owner_id == user.id:
            return True
        return self.repository.user_has_kb_membership(
            user.id,
            knowledge_base_id,
            {KnowledgeBaseMemberRole.OWNER, KnowledgeBaseMemberRole.MANAGER},
        )

    def filter_accessible_knowledge_base_ids(
        self,
        user: User,
        knowledge_base_ids: Iterable[uuid.UUID],
    ) -> list[uuid.UUID]:
        return [
            knowledge_base_id
            for knowledge_base_id in knowledge_base_ids
            if self.can_access_knowledge_base(user, knowledge_base_id)
        ]

    def apply_knowledge_base_scope(self, user: User, knowledge_base_ids: Iterable[uuid.UUID]):
        return self.filter_accessible_knowledge_base_ids(user, knowledge_base_ids)

    def apply_document_scope(self, user: User, knowledge_base_ids: Iterable[uuid.UUID]):
        return self.filter_accessible_knowledge_base_ids(user, knowledge_base_ids)

    def apply_chunk_scope(self, user: User, knowledge_base_ids: Iterable[uuid.UUID]):
        return self.filter_accessible_knowledge_base_ids(user, knowledge_base_ids)
