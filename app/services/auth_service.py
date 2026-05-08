from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user import User
from app.repositories.users import UserRepository


class AuthService:
    def __init__(self, db: Session):
        self.users = UserRepository(db)

    def authenticate(self, username_or_email: str, password: str) -> User | None:
        user = self.users.get_by_username_or_email(username_or_email)
        if user is None or not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

