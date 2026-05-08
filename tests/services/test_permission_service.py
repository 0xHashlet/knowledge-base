import uuid

from app.models.knowledge_base import (
    KnowledgeBase,
    KnowledgeBaseMember,
    KnowledgeBaseMemberRole,
    KnowledgeBaseVisibility,
)
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from app.services.permission_service import PermissionService


class FakePermissionRepository:
    def __init__(self, knowledge_base: KnowledgeBase | None = None):
        self.knowledge_base = knowledge_base

    def get_user_permissions(self, user_id: uuid.UUID) -> set[str]:
        return {"knowledge_base:read", "documents:upload"}

    def get_knowledge_base(self, knowledge_base_id: uuid.UUID) -> KnowledgeBase | None:
        return self.knowledge_base

    def user_has_kb_membership(
        self,
        user_id: uuid.UUID,
        knowledge_base_id: uuid.UUID,
        allowed_roles: set[KnowledgeBaseMemberRole] | None = None,
    ) -> bool:
        knowledge_base = self.get_knowledge_base(knowledge_base_id)
        if knowledge_base is None:
            return False
        for member in knowledge_base.members:
            if member.user_id == user_id and member.knowledge_base_id == knowledge_base_id:
                return allowed_roles is None or member.role in allowed_roles
        return False


def test_superuser_has_every_permission():
    user = User(email="admin@example.com", username="admin", hashed_password="x", is_superuser=True)
    service = PermissionService(FakePermissionRepository())

    assert service.has_permission(user, "anything", "manage")


def test_role_permission_matches_resource_action():
    user = User(email="u@example.com", username="u", hashed_password="x")
    role = Role(name="operator")
    role.permissions = [Permission(resource="knowledge_base", action="read")]
    user.roles = [role]
    service = PermissionService(FakePermissionRepository())

    assert service.has_permission(user, "knowledge_base", "read")
    assert not service.has_permission(user, "knowledge_base", "delete")


def test_private_knowledge_base_requires_membership_or_owner():
    owner_id = uuid.uuid4()
    member_id = uuid.uuid4()
    outsider_id = uuid.uuid4()
    kb_id = uuid.uuid4()
    kb = KnowledgeBase(
        id=kb_id,
        name="Private KB",
        owner_id=owner_id,
        visibility=KnowledgeBaseVisibility.PRIVATE,
    )
    kb.members = [
        KnowledgeBaseMember(
            knowledge_base_id=kb_id,
            user_id=member_id,
            role=KnowledgeBaseMemberRole.VIEWER,
        )
    ]
    service = PermissionService(FakePermissionRepository(kb))

    owner = User(id=owner_id, email="o@example.com", username="o", hashed_password="x")
    member = User(id=member_id, email="m@example.com", username="m", hashed_password="x")
    outsider = User(id=outsider_id, email="x@example.com", username="x", hashed_password="x")

    assert service.can_access_knowledge_base(owner, kb_id)
    assert service.can_access_knowledge_base(member, kb_id)
    assert not service.can_access_knowledge_base(outsider, kb_id)


def test_permission_filter_scope_keeps_only_accessible_knowledge_bases():
    user_id = uuid.uuid4()
    allowed_id = uuid.uuid4()
    denied_id = uuid.uuid4()
    allowed = KnowledgeBase(
        id=allowed_id,
        name="Allowed",
        owner_id=uuid.uuid4(),
        visibility=KnowledgeBaseVisibility.PRIVATE,
    )
    allowed.members = [
        KnowledgeBaseMember(
            knowledge_base_id=allowed_id,
            user_id=user_id,
            role=KnowledgeBaseMemberRole.VIEWER,
        )
    ]
    denied = KnowledgeBase(
        id=denied_id,
        name="Denied",
        owner_id=uuid.uuid4(),
        visibility=KnowledgeBaseVisibility.PRIVATE,
    )
    denied.members = []

    class MultiKbRepo(FakePermissionRepository):
        def get_knowledge_base(self, knowledge_base_id: uuid.UUID) -> KnowledgeBase | None:
            return {allowed_id: allowed, denied_id: denied}.get(knowledge_base_id)

    service = PermissionService(MultiKbRepo())
    user = User(id=user_id, email="u@example.com", username="u", hashed_password="x")

    assert service.filter_accessible_knowledge_base_ids(
        user,
        [allowed_id, denied_id],
    ) == [allowed_id]
