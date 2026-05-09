import json as _json
import uuid as _uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_permission_service, get_qa_service
from app.models.user import User
from app.schemas.qa import QaAskRequest, QaAskResponse
from app.services.permission_service import PermissionService
from app.services.qa_service import QaService

router = APIRouter(tags=["qa"])


@router.post("/qa/ask", response_model=QaAskResponse)
def ask_question(
    req: QaAskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    permission_service: PermissionService = Depends(get_permission_service),
    qa_service: QaService = Depends(get_qa_service),
):
    accessible = permission_service.filter_accessible_knowledge_base_ids(
        current_user, req.knowledge_base_ids
    )
    if not accessible:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问指定的知识库",
        )

    result = qa_service.ask(
        user=current_user,
        question=req.question,
        knowledge_base_ids=accessible,
        session_id=req.session_id,
    )
    return {"session_id": result["session_id"], "message": result["message"]}


@router.post("/qa/ask-stream")
def ask_question_stream(
    req: QaAskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    permission_service: PermissionService = Depends(get_permission_service),
    qa_service: QaService = Depends(get_qa_service),
):
    accessible = permission_service.filter_accessible_knowledge_base_ids(
        current_user, req.knowledge_base_ids
    )
    if not accessible:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问指定的知识库",
        )

    def generate():
        full_answer = ""
        session_id = None
        message_id = str(_uuid.uuid4())
        citations = []
        try:
            for chunk in qa_service.ask_stream(
                user=current_user,
                question=req.question,
                knowledge_base_ids=accessible,
                session_id=req.session_id,
            ):
                if isinstance(chunk, dict):
                    # Metadata event (session_id, citations, done)
                    if "session_id" in chunk:
                        session_id = chunk["session_id"]
                    if "citations" in chunk:
                        citations = chunk["citations"]
                    if chunk.get("done"):
                        yield f"data: {_json.dumps({'done': True, 'session_id': str(session_id), 'message_id': message_id, 'citations': citations}, default=str)}\n\n"
                        return
                else:
                    full_answer += chunk
                    yield f"data: {_json.dumps({'token': chunk})}\n\n"
        except Exception as exc:
            yield f"data: {_json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
