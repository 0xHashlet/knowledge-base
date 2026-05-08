from app.models.department import Department
from app.repositories.base import SqlAlchemyRepository


class DepartmentRepository(SqlAlchemyRepository[Department]):
    model = Department

