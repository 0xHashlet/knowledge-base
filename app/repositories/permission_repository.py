import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.knowledge_base import (
    KnowledgeBase,
    KnowledgeBaseMember,
    KnowledgeBaseMemberRole,
)
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User


class PermissionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_permissions(self, user_id: uuid.UUID) -> set[str]:
        statement = (
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.id == user_id)
        )
        user = self.db.scalars(statement).first()
        if user is None:
            return set()
        return {
            self.format_permission(permission)
            for role in user.roles
            for permission in role.permissions
        }

    def get_knowledge_base(self, knowledge_base_id: uuid.UUID) -> KnowledgeBase | None:
        statement = (
            select(KnowledgeBase)
            .options(selectinload(KnowledgeBase.members))
            .where(KnowledgeBase.id == knowledge_base_id)
        )
        return self.db.scalars(statement).first()

    def user_has_kb_membership(
        self,
        user_id: uuid.UUID,
        knowledge_base_id: uuid.UUID,
        allowed_roles: set[KnowledgeBaseMemberRole] | None = None,
    ) -> bool:
        statement = select(KnowledgeBaseMember).where(
            KnowledgeBaseMember.user_id == user_id,
            KnowledgeBaseMember.knowledge_base_id == knowledge_base_id,
        )
        member = self.db.scalars(statement).first()
        if member is None:
            return False
        return allowed_roles is None or member.role in allowed_roles

    @staticmethod
    def format_permission(permission: Permission) -> str:
        return f"{permission.resource}:{permission.action}"
