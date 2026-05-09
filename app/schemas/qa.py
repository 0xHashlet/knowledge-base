import uuid
from datetime import datetime

from app.schemas.common import ApiModel


class CitationRead(ApiModel):
    document_id: uuid.UUID
    document_title: str
    chunk_id: uuid.UUID
    chunk_text: str
    relevance_score: float | None = None


class QaMessageRead(ApiModel):
    id: uuid.UUID
    role: str
    content: str
    citations: list[CitationRead] = []
    created_at: datetime


class QaAskRequest(ApiModel):
    question: str
    knowledge_base_ids: list[uuid.UUID]
    session_id: uuid.UUID | None = None


class QaAskResponse(ApiModel):
    session_id: uuid.UUID
    message: QaMessageRead
