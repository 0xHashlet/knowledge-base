import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.role_service import RoleService
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(require_admin)])


@router.get("", response_model=list[UserRead])
def list_users(
    offset: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[User]:
    return UserService(db).list(offset=offset, limit=limit)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(data: UserCreate, db: Session = Depends(get_db)) -> User:
    return UserService(db).create(data)


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)) -> User:
    user = UserService(db).get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserRead)
def update_user(user_id: uuid.UUID, data: UserUpdate, db: Session = Depends(get_db)) -> User:
    service = UserService(db)
    user = service.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return service.update(user, data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: uuid.UUID, db: Session = Depends(get_db)) -> Response:
    service = UserService(db)
    user = service.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    service.delete(user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{user_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def assign_user_role(
    user_id: uuid.UUID,
    role_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> Response:
    role = RoleService(db).assign_user_role(user_id, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="User or role not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

