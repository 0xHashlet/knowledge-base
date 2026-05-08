import uuid

import pytest
from fastapi import HTTPException

from app.api.deps import require_admin, require_knowledge_base_member
from app.models.user import User


def test_require_admin_allows_superuser():
    user = User(email="admin@example.com", username="admin", hashed_password="x", is_superuser=True)

    assert require_admin(user) is user


def test_require_admin_rejects_normal_user():
    user = User(email="u@example.com", username="u", hashed_password="x", is_superuser=False)

    with pytest.raises(HTTPException) as exc:
        require_admin(user)

    assert exc.value.status_code == 403


def test_require_knowledge_base_member_uses_permission_service():
    kb_id = uuid.uuid4()
    user = User(id=uuid.uuid4(), email="u@example.com", username="u", hashed_password="x")

    class FakePermissionService:
        def can_access_knowledge_base(self, current_user, knowledge_base_id):
            return current_user is user and knowledge_base_id == kb_id

    dependency = require_knowledge_base_member(kb_id)

    assert dependency(user, FakePermissionService()) is user
