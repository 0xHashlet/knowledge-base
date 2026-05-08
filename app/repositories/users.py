import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.user import User
from app.repositories.base import SqlAlchemyRepository


class UserRepository(SqlAlchemyRepository[User]):
    model = User

    def __init__(self, db: Session):
        super().__init__(db)

    def get_with_roles(self, user_id: uuid.UUID) -> User | None:
        statement = (
            select(User)
            .options(selectinload(User.roles))
            .where(User.id == user_id)
        )
        return self.db.scalars(statement).first()

    def get_by_username_or_email(self, value: str) -> User | None:
        statement = select(User).where(or_(User.username == value, User.email == value))
        return self.db.scalars(statement).first()

