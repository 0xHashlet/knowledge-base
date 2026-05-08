from collections.abc import Generator
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.user import User
from app.repositories.permission_repository import PermissionRepository
from app.repositories.users import UserRepository
from app.services.permission_service import PermissionService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_permission_service(db: Session = Depends(get_db)) -> PermissionService:
    return PermissionService(PermissionRepository(db))


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id = uuid.UUID(str(payload.get("sub")))
    except (TypeError, ValueError):
        raise credentials_error

    user = UserRepository(db).get_with_roles(user_id)
    if user is None or not user.is_active:
        raise credentials_error
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required",
        )
    return current_user


def require_knowledge_base_member(knowledge_base_id: uuid.UUID):
    def dependency(
        current_user: User = Depends(get_current_user),
        permission_service: PermissionService = Depends(get_permission_service),
    ) -> User:
        if not permission_service.can_access_knowledge_base(current_user, knowledge_base_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Knowledge base access denied",
            )
        return current_user

    return dependency
