import uuid

from pydantic import EmailStr, Field

from app.schemas.common import ApiModel


class UserBase(ApiModel):
    email: EmailStr
    username: str = Field(min_length=2, max_length=80)
    full_name: str | None = Field(default=None, max_length=120)
    is_active: bool = True
    is_superuser: bool = False
    department_id: uuid.UUID | None = None


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(ApiModel):
    email: EmailStr | None = None
    username: str | None = Field(default=None, min_length=2, max_length=80)
    full_name: str | None = Field(default=None, max_length=120)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    is_active: bool | None = None
    is_superuser: bool | None = None
    department_id: uuid.UUID | None = None


class UserRead(UserBase):
    id: uuid.UUID

