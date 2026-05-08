from app.models.permission import Permission
from app.repositories.base import SqlAlchemyRepository


class PermissionRepository(SqlAlchemyRepository[Permission]):
    model = Permission

