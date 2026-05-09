import uuid

from sqlalchemy.orm import Session

from app.models.knowledge_base import KnowledgeBase, KnowledgeBaseMember
from app.models.user import User
from app.repositories.knowledge_bases import KnowledgeBaseRepository
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseMemberCreate,
    KnowledgeBaseUpdate,
)


class KnowledgeBaseService:
    def __init__(self, db: Session):
        self.repository = KnowledgeBaseRepository(db)

    def get(self, knowledge_base_id: uuid.UUID) -> KnowledgeBase | None:
        return self.repository.get(knowledge_base_id)

    def list(self, *, offset: int = 0, limit: int = 100) -> list[KnowledgeBase]:
        return self.repository.list(offset=offset, limit=limit)

    def create(self, data: KnowledgeBaseCreate, owner: User) -> KnowledgeBase:
        knowledge_base = KnowledgeBase(**data.model_dump(), owner_id=owner.id)
        return self.repository.add(knowledge_base)

    def update(
        self,
        knowledge_base: KnowledgeBase,
        data: KnowledgeBaseUpdate,
    ) -> KnowledgeBase:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(knowledge_base, field, value)
        return self.repository.commit(knowledge_base)

    def delete(self, knowledge_base: KnowledgeBase) -> None:
        self.repository.delete(knowledge_base)

    def grant_member(
        self,
        knowledge_base_id: uuid.UUID,
        data: KnowledgeBaseMemberCreate,
    ) -> KnowledgeBaseMember:
        member = self.repository.get_member(knowledge_base_id, data.user_id)
        if member is None:
            member = KnowledgeBaseMember(
                knowledge_base_id=knowledge_base_id,
                user_id=data.user_id,
                role=data.role,
            )
            return self.repository.add_member(member)
        member.role = data.role
        self.repository.db.commit()
        self.repository.db.refresh(member)
        return member

    def list_members(self, knowledge_base_id: uuid.UUID) -> list[KnowledgeBaseMember]:
        return self.repository.list_members(knowledge_base_id)

    def remove_member(self, knowledge_base_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        member = self.repository.get_member(knowledge_base_id, user_id)
        if member is None:
            return False
        self.repository.remove_member(member)
        return True

