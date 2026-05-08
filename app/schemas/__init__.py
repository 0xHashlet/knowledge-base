"""Pydantic API schemas will be added with each endpoint slice."""
from app.schemas.department import DepartmentCreate, DepartmentRead, DepartmentUpdate
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseMemberCreate,
    KnowledgeBaseMemberRead,
    KnowledgeBaseRead,
    KnowledgeBaseUpdate,
)
from app.schemas.permission import PermissionCreate, PermissionRead, PermissionUpdate
from app.schemas.role import RoleCreate, RoleRead, RoleUpdate
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserRead, UserUpdate

__all__ = [
    "DepartmentCreate",
    "DepartmentRead",
    "DepartmentUpdate",
    "KnowledgeBaseCreate",
    "KnowledgeBaseMemberCreate",
    "KnowledgeBaseMemberRead",
    "KnowledgeBaseRead",
    "KnowledgeBaseUpdate",
    "PermissionCreate",
    "PermissionRead",
    "PermissionUpdate",
    "RoleCreate",
    "RoleRead",
    "RoleUpdate",
    "Token",
    "UserCreate",
    "UserRead",
    "UserUpdate",
]
