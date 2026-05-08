import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentRead, DepartmentUpdate
from app.services.department_service import DepartmentService

router = APIRouter(
    prefix="/departments",
    tags=["departments"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=list[DepartmentRead])
def list_departments(offset: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return DepartmentService(db).list(offset=offset, limit=limit)


@router.post("", response_model=DepartmentRead, status_code=status.HTTP_201_CREATED)
def create_department(data: DepartmentCreate, db: Session = Depends(get_db)) -> Department:
    return DepartmentService(db).create(data)


@router.get("/{department_id}", response_model=DepartmentRead)
def get_department(department_id: uuid.UUID, db: Session = Depends(get_db)) -> Department:
    department = DepartmentService(db).get(department_id)
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")
    return department


@router.patch("/{department_id}", response_model=DepartmentRead)
def update_department(
    department_id: uuid.UUID,
    data: DepartmentUpdate,
    db: Session = Depends(get_db),
) -> Department:
    service = DepartmentService(db)
    department = service.get(department_id)
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")
    return service.update(department, data)


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_department(department_id: uuid.UUID, db: Session = Depends(get_db)) -> Response:
    service = DepartmentService(db)
    department = service.get(department_id)
    if department is None:
        raise HTTPException(status_code=404, detail="Department not found")
    service.delete(department)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

