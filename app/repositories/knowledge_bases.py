import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.knowledge_base import KnowledgeBase, KnowledgeBaseMember
from app.repositories.base import SqlAlchemyRepository


class KnowledgeBaseRepository(SqlAlchemyRepository[KnowledgeBase]):
    model = KnowledgeBase

    def get_with_members(self, knowledge_base_id: uuid.UUID) -> KnowledgeBase | None:
        statement = (
            select(KnowledgeBase)
            .options(selectinload(KnowledgeBase.members))
            .where(KnowledgeBase.id == knowledge_base_id)
        )
        return self.db.scalars(statement).first()

    def get_member(
        self,
        knowledge_base_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> KnowledgeBaseMember | None:
        statement = select(KnowledgeBaseMember).where(
            KnowledgeBaseMember.knowledge_base_id == knowledge_base_id,
            KnowledgeBaseMember.user_id == user_id,
        )
        return self.db.scalars(statement).first()

    def add_member(self, member: KnowledgeBaseMember) -> KnowledgeBaseMember:
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        return member

