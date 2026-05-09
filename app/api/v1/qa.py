from fastapi import APIRouter, Depends
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
    # Verify user can access at least one of the requested KBs
    accessible = permission_service.filter_accessible_knowledge_base_ids(
        current_user, req.knowledge_base_ids
    )
    if not accessible:
        from fastapi import HTTPException, status
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
