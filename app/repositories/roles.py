import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.permission import Permission
from app.models.role import Role
from app.models.user import User
from app.repositories.base import SqlAlchemyRepository


class RoleRepository(SqlAlchemyRepository[Role]):
    model = Role

    def get_with_permissions(self, role_id: uuid.UUID) -> Role | None:
        statement = select(Role).options(selectinload(Role.permissions)).where(Role.id == role_id)
        return self.db.scalars(statement).first()

    def get_permission(self, permission_id: uuid.UUID) -> Permission | None:
        return self.db.get(Permission, permission_id)

    def get_user(self, user_id: uuid.UUID) -> User | None:
        statement = select(User).options(selectinload(User.roles)).where(User.id == user_id)
        return self.db.scalars(statement).first()

