"""Repository layer package."""
from app.repositories.departments import DepartmentRepository
from app.repositories.knowledge_bases import KnowledgeBaseRepository
from app.repositories.permission_repository import PermissionRepository
from app.repositories.permissions import PermissionRepository as PermissionCrudRepository
from app.repositories.roles import RoleRepository
from app.repositories.users import UserRepository

__all__ = [
    "DepartmentRepository",
    "KnowledgeBaseRepository",
    "PermissionCrudRepository",
    "PermissionRepository",
    "RoleRepository",
    "UserRepository",
]
