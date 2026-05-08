from app.schemas.common import ApiModel


class Token(ApiModel):
    access_token: str
    token_type: str = "bearer"

