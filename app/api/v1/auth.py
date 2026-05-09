from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import get_settings
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserRead
from app.services.auth_service import AuthService
from app.services.sso_service import OidcConfig, SsoService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    user = AuthService(db).authenticate(form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(str(user.id)))


@router.get("/sso/login")
def sso_login(db: Session = Depends(get_db)):
    settings = get_settings()
    config = _build_oidc_config(settings)
    sso = SsoService(db, config)
    if not sso.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SSO is not configured")
    return RedirectResponse(url=sso.get_authorization_url())


@router.get("/sso/callback", response_model=Token)
def sso_callback(code: str, db: Session = Depends(get_db)):
    settings = get_settings()
    config = _build_oidc_config(settings)
    sso = SsoService(db, config)
    if not sso.enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SSO is not configured")
    try:
        token, _ = sso.handle_callback(code)
        return Token(access_token=token)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


def _build_oidc_config(settings) -> OidcConfig | None:
    if not settings.oidc_client_id:
        return None
    return OidcConfig(
        client_id=settings.oidc_client_id,
        client_secret=settings.oidc_client_secret,
        discovery_url=settings.oidc_discovery_url,
        redirect_uri=settings.oidc_redirect_uri,
    )

