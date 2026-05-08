import uuid

from sqlalchemy.orm import Session

from app.models.role import Role
from app.repositories.roles import RoleRepository
from app.schemas.role import RoleCreate, RoleUpdate


class RoleService:
    def __init__(self, db: Session):
        self.repository = RoleRepository(db)

    def get(self, role_id: uuid.UUID) -> Role | None:
        return self.repository.get(role_id)

    def list(self, *, offset: int = 0, limit: int = 100) -> list[Role]:
        return self.repository.list(offset=offset, limit=limit)

    def create(self, data: RoleCreate) -> Role:
        return self.repository.add(Role(**data.model_dump()))

    def update(self, role: Role, data: RoleUpdate) -> Role:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(role, field, value)
        return self.repository.commit(role)

    def delete(self, role: Role) -> None:
        self.repository.delete(role)

    def assign_user_role(self, user_id: uuid.UUID, role_id: uuid.UUID) -> Role | None:
        user = self.repository.get_user(user_id)
        role = self.repository.get(role_id)
        if user is None or role is None:
            return None
        if role not in user.roles:
            user.roles.append(role)
            self.repository.db.commit()
        return role

    def assign_role_permission(self, role_id: uuid.UUID, permission_id: uuid.UUID) -> Role | None:
        role = self.repository.get_with_permissions(role_id)
        permission = self.repository.get_permission(permission_id)
        if role is None or permission is None:
            return None
        if permission not in role.permissions:
            role.permissions.append(permission)
            self.repository.db.commit()
        return role

