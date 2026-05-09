from __future__ import annotations

import json
import uuid
from collections.abc import Generator

from app.models.qa import QaSession, QaMessage, QaMessageRole
from app.models.user import User


class QaService:
    def __init__(
        self,
        db,
        retrieval_service,
        llm_service,
        embedding_service,
        redis_client,
        chat_ttl: int = 3600,
    ):
        self.db = db
        self.retrieval = retrieval_service
        self.llm = llm_service
        self.embedding = embedding_service
        self.redis = redis_client
        self.chat_ttl = chat_ttl

    def ask(
        self,
        *,
        user: User,
        question: str,
        knowledge_base_ids: list[uuid.UUID],
        session_id: uuid.UUID | None = None,
    ) -> dict:
        # 1. Get conversation history
        history = self._get_history(session_id) if session_id else []

        # 2. Generate query embedding for vector search. If the embedding
        # service is unavailable in local/dev environments, keep keyword
        # retrieval available instead of failing the whole QA request.
        try:
            query_vector = self.embedding.embed([question])[0]
        except Exception:
            query_vector = None

        # 3. Retrieve relevant chunks (permission-filtered)
        results = self.retrieval.retrieve(
            user=user,
            knowledge_base_ids=knowledge_base_ids,
            query=question,
            query_vector=query_vector,
            limit=10,
        )

        # 4. Build context from retrieved chunks
        chunks = [r.chunk for r in results]
        context = "\n\n---\n\n".join(chunk.content for chunk in chunks)

        # 5. Generate answer with LLM (handles empty context internally)
        answer = self.llm.generate(context=context, question=question)

        # 6. Build citations
        citations = []
        for r in results:
            doc = getattr(r.chunk, "document", None)
            doc_title = getattr(doc, "title", "") if doc else ""
            citations.append({
                "document_id": str(r.chunk.document_id),
                "document_title": doc_title,
                "chunk_id": str(r.chunk.id),
                "chunk_text": r.chunk.content[:200],
                "relevance_score": r.score,
            })

        # 7. Save to database and Redis
        return self._save(
            user=user,
            question=question,
            answer=answer,
            citations=citations,
            knowledge_base_ids=knowledge_base_ids,
            session_id=session_id,
            history=history,
        )

    def ask_stream(
        self,
        *,
        user: User,
        question: str,
        knowledge_base_ids: list[uuid.UUID],
        session_id: uuid.UUID | None = None,
    ) -> Generator:
        history = self._get_history(session_id) if session_id else []

        try:
            query_vector = self.embedding.embed([question])[0]
        except Exception:
            query_vector = None

        results = self.retrieval.retrieve(
            user=user,
            knowledge_base_ids=knowledge_base_ids,
            query=question,
            query_vector=query_vector,
            limit=10,
        )

        chunks = [r.chunk for r in results]
        context = "\n\n---\n\n".join(chunk.content for chunk in chunks)

        citations = []
        for r in results:
            doc = getattr(r.chunk, "document", None)
            doc_title = getattr(doc, "title", "") if doc else ""
            citations.append({
                "document_id": str(r.chunk.document_id),
                "document_title": doc_title,
                "chunk_id": str(r.chunk.id),
                "chunk_text": r.chunk.content[:200],
                "relevance_score": r.score,
            })

        # Stream tokens
        full_answer = ""
        for token in self.llm.generate_stream(context=context, question=question):
            full_answer += token
            yield token

        # Save and yield metadata
        saved = self._save(
            user=user,
            question=question,
            answer=full_answer,
            citations=citations,
            knowledge_base_ids=knowledge_base_ids,
            session_id=session_id,
            history=history,
        )
        yield {"session_id": str(saved["session_id"]), "citations": citations, "done": True}

    def _get_history(self, session_id: uuid.UUID) -> list[dict]:
        key = f"chat:{session_id}"
        try:
            data = self.redis.get(key)
            if data:
                return json.loads(data)
        except Exception:
            pass
        # Fallback to DB
        session = self.db.get(QaSession, session_id)
        if session and session.messages:
            return [
                {"role": m.role.value, "content": m.content}
                for m in session.messages[-10:]
            ]
        return []

    def _save(
        self,
        *,
        user,
        question,
        answer,
        citations,
        knowledge_base_ids,
        session_id,
        history,
    ) -> dict:
        if not session_id:
            session = QaSession(
                user_id=user.id,
                knowledge_base_id=knowledge_base_ids[0] if knowledge_base_ids else None,
                title=question[:100],
            )
            self.db.add(session)
            self.db.flush()
            session_id = session.id

        user_msg = QaMessage(
            session_id=session_id,
            role=QaMessageRole.USER,
            content=question,
        )
        assistant_msg = QaMessage(
            session_id=session_id,
            role=QaMessageRole.ASSISTANT,
            content=answer,
            citations=citations,
        )
        self.db.add_all([user_msg, assistant_msg])
        self.db.commit()
        self.db.refresh(assistant_msg)

        # Update Redis cache
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": answer})
        try:
            self.redis.setex(
                f"chat:{session_id}",
                self.chat_ttl,
                json.dumps(history, ensure_ascii=False),
            )
        except Exception:
            pass

        return {
            "session_id": session_id,
            "message": self._to_message_read(assistant_msg),
        }

    @staticmethod
    def _to_message_read(msg: QaMessage) -> dict:
        from app.schemas.qa import CitationRead, QaMessageRead

        return QaMessageRead(
            id=msg.id,
            role=msg.role.value,
            content=msg.content,
            citations=[
                CitationRead(**c) if isinstance(c, dict) else c
                for c in (msg.citations or [])
            ],
            created_at=msg.created_at,
        )
