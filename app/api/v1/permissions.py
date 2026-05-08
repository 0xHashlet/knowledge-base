import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.models.permission import Permission
from app.schemas.permission import PermissionCreate, PermissionRead, PermissionUpdate
from app.services.permission_crud_service import PermissionCrudService

router = APIRouter(
    prefix="/permissions",
    tags=["permissions"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=list[PermissionRead])
def list_permissions(
    offset: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[Permission]:
    return PermissionCrudService(db).list(offset=offset, limit=limit)


@router.post("", response_model=PermissionRead, status_code=status.HTTP_201_CREATED)
def create_permission(data: PermissionCreate, db: Session = Depends(get_db)) -> Permission:
    return PermissionCrudService(db).create(data)


@router.get("/{permission_id}", response_model=PermissionRead)
def get_permission(permission_id: uuid.UUID, db: Session = Depends(get_db)) -> Permission:
    permission = PermissionCrudService(db).get(permission_id)
    if permission is None:
        raise HTTPException(status_code=404, detail="Permission not found")
    return permission


@router.patch("/{permission_id}", response_model=PermissionRead)
def update_permission(
    permission_id: uuid.UUID,
    data: PermissionUpdate,
    db: Session = Depends(get_db),
) -> Permission:
    service = PermissionCrudService(db)
    permission = service.get(permission_id)
    if permission is None:
        raise HTTPException(status_code=404, detail="Permission not found")
    return service.update(permission, data)


@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_permission(permission_id: uuid.UUID, db: Session = Depends(get_db)) -> Response:
    service = PermissionCrudService(db)
    permission = service.get(permission_id)
    if permission is None:
        raise HTTPException(status_code=404, detail="Permission not found")
    service.delete(permission)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

