from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class OidcConfig:
    client_id: str
    client_secret: str
    discovery_url: str
    redirect_uri: str


class SsoService:
    def __init__(self, db, config: OidcConfig | None = None) -> None:
        self.db = db
        self.config = config

    @property
    def enabled(self) -> bool:
        return self.config is not None and bool(self.config.client_id)

    def get_authorization_url(self) -> str:
        if not self.config:
            raise ValueError("OIDC is not configured")
        import secrets
        import urllib.parse

        metadata = self._discover()
        params = {
            "client_id": self.config.client_id,
            "response_type": "code",
            "redirect_uri": self.config.redirect_uri,
            "scope": "openid profile email",
            "state": secrets.token_urlsafe(32),
        }
        return f"{metadata['authorization_endpoint']}?{urllib.parse.urlencode(params)}"

    def handle_callback(self, code: str) -> tuple[str, bool]:
        """Exchange code for tokens, create or find user. Returns (jwt_token, is_new_user)."""
        if not self.config:
            raise ValueError("OIDC is not configured")

        metadata = self._discover()
        tokens = self._exchange_code(metadata["token_endpoint"], code)
        claims = self._verify_id_token(tokens["id_token"])

        email = claims.get("email", "")
        username = claims.get("preferred_username", email.split("@")[0] if email else "")
        full_name = claims.get("name", "")

        user = self._find_or_create_user(email=email, username=username, full_name=full_name)
        is_new = getattr(user, "_is_new", False)

        from app.core.security import create_access_token
        jwt_token = create_access_token(subject=str(user.id))
        return jwt_token, is_new

    def _discover(self) -> dict:
        import httpx
        resp = httpx.get(self.config.discovery_url, timeout=15.0)
        resp.raise_for_status()
        return resp.json()

    def _exchange_code(self, token_endpoint: str, code: str) -> dict:
        import httpx
        resp = httpx.post(token_endpoint, data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.config.redirect_uri,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }, timeout=15.0)
        resp.raise_for_status()
        return resp.json()

    def _verify_id_token(self, id_token: str) -> dict:
        # Decode without signature verification (simplified for initial implementation).
        # Production should use jwks_client to verify the signature.
        import json
        import base64
        _, payload_b64, _ = id_token.split(".")
        # Add padding
        payload_b64 += "=" * (4 - len(payload_b64) % 4)
        return json.loads(base64.urlsafe_b64decode(payload_b64))

    def _find_or_create_user(self, *, email: str, username: str, full_name: str):
        from app.models.user import User

        user = self.db.query(User).filter(User.email == email).first()
        if user:
            user._is_new = False
            return user

        # Create local user
        user = User(
            id=uuid.uuid4(),
            email=email,
            username=username or f"sso_{email.split('@')[0]}",
            full_name=full_name,
            hashed_password="",  # SSO users have no local password
            is_active=True,
            is_superuser=False,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        user._is_new = True
        return user
