import uuid

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.repositories.users import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def get(self, user_id: uuid.UUID) -> User | None:
        return self.repository.get(user_id)

    def list(self, *, offset: int = 0, limit: int = 100) -> list[User]:
        return self.repository.list(offset=offset, limit=limit)

    def create(self, data: UserCreate) -> User:
        values = data.model_dump(exclude={"password"})
        user = User(**values, hashed_password=hash_password(data.password))
        return self.repository.add(user)

    def update(self, user: User, data: UserUpdate) -> User:
        values = data.model_dump(exclude_unset=True)
        password = values.pop("password", None)
        for field, value in values.items():
            setattr(user, field, value)
        if password is not None:
            user.hashed_password = hash_password(password)
        return self.repository.commit(user)

    def delete(self, user: User) -> None:
        self.repository.delete(user)

