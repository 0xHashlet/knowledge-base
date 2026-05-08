import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.models.role import Role
from app.schemas.role import RoleCreate, RoleRead, RoleUpdate
from app.services.role_service import RoleService

router = APIRouter(prefix="/roles", tags=["roles"], dependencies=[Depends(require_admin)])


@router.get("", response_model=list[RoleRead])
def list_roles(offset: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> list[Role]:
    return RoleService(db).list(offset=offset, limit=limit)


@router.post("", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
def create_role(data: RoleCreate, db: Session = Depends(get_db)) -> Role:
    return RoleService(db).create(data)


@router.get("/{role_id}", response_model=RoleRead)
def get_role(role_id: uuid.UUID, db: Session = Depends(get_db)) -> Role:
    role = RoleService(db).get(role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.patch("/{role_id}", response_model=RoleRead)
def update_role(role_id: uuid.UUID, data: RoleUpdate, db: Session = Depends(get_db)) -> Role:
    service = RoleService(db)
    role = service.get(role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return service.update(role, data)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(role_id: uuid.UUID, db: Session = Depends(get_db)) -> Response:
    service = RoleService(db)
    role = service.get(role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    service.delete(role)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{role_id}/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def assign_role_permission(
    role_id: uuid.UUID,
    permission_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> Response:
    role = RoleService(db).assign_role_permission(role_id, permission_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role or permission not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

