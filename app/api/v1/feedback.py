import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.feedback import AnswerFeedback, FeedbackRating
from app.models.qa import QaMessage
from app.models.user import User
from app.schemas.feedback import FeedbackCreate, FeedbackRead

router = APIRouter(tags=["feedback"])


@router.post("/feedback", response_model=FeedbackRead)
def submit_feedback(
    req: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if req.rating not in ("up", "down"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="rating 必须为 up 或 down")

    try:
        message_id = uuid.UUID(req.message_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的 message_id")

    message = db.get(QaMessage, message_id)
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="消息不存在")

    feedback = AnswerFeedback(
        message_id=message_id,
        user_id=current_user.id,
        rating=FeedbackRating(req.rating),
        comment=req.comment,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return FeedbackRead(
        id=str(feedback.id),
        message_id=str(feedback.message_id),
        user_id=str(feedback.user_id),
        rating=feedback.rating.value,
        comment=feedback.comment,
    )
