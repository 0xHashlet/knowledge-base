from app.schemas.common import ApiModel


class FeedbackCreate(ApiModel):
    message_id: str
    rating: str  # "up" | "down"
    comment: str | None = None


class FeedbackRead(ApiModel):
    id: str
    message_id: str
    user_id: str
    rating: str
    comment: str | None = None
