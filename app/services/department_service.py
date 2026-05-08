import uuid

from sqlalchemy.orm import Session

from app.models.department import Department
from app.repositories.departments import DepartmentRepository
from app.schemas.department import DepartmentCreate, DepartmentUpdate


class DepartmentService:
    def __init__(self, db: Session):
        self.repository = DepartmentRepository(db)

    def get(self, department_id: uuid.UUID) -> Department | None:
        return self.repository.get(department_id)

    def list(self, *, offset: int = 0, limit: int = 100) -> list[Department]:
        return self.repository.list(offset=offset, limit=limit)

    def create(self, data: DepartmentCreate) -> Department:
        return self.repository.add(Department(**data.model_dump()))

    def update(self, department: Department, data: DepartmentUpdate) -> Department:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(department, field, value)
        return self.repository.commit(department)

    def delete(self, department: Department) -> None:
        self.repository.delete(department)

