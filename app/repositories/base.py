import uuid
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

ModelT = TypeVar("ModelT")


class SqlAlchemyRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, db: Session):
        self.db = db

    def get(self, item_id: uuid.UUID) -> ModelT | None:
        return self.db.get(self.model, item_id)

    def list(self, *, offset: int = 0, limit: int = 100) -> list[ModelT]:
        statement = select(self.model).offset(offset).limit(limit)
        return list(self.db.scalars(statement).all())

    def add(self, item: ModelT) -> ModelT:
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, item: ModelT) -> None:
        self.db.delete(item)
        self.db.commit()

    def commit(self, item: ModelT) -> ModelT:
        self.db.commit()
        self.db.refresh(item)
        return item

