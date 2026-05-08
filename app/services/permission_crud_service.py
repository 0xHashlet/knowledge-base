import uuid

from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.repositories.permissions import PermissionRepository
from app.schemas.permission import PermissionCreate, PermissionUpdate


class PermissionCrudService:
    def __init__(self, db: Session):
        self.repository = PermissionRepository(db)

    def get(self, permission_id: uuid.UUID) -> Permission | None:
        return self.repository.get(permission_id)

    def list(self, *, offset: int = 0, limit: int = 100) -> list[Permission]:
        return self.repository.list(offset=offset, limit=limit)

    def create(self, data: PermissionCreate) -> Permission:
        return self.repository.add(Permission(**data.model_dump()))

    def update(self, permission: Permission, data: PermissionUpdate) -> Permission:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(permission, field, value)
        return self.repository.commit(permission)

    def delete(self, permission: Permission) -> None:
        self.repository.delete(permission)

