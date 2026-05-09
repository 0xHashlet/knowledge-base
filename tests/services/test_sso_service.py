import pytest
from app.services.sso_service import OidcConfig, SsoService


def test_sso_disabled_without_config():
    svc = SsoService(db=None, config=None)
    assert svc.enabled is False


def test_sso_disabled_with_empty_client_id():
    config = OidcConfig(client_id="", client_secret="", discovery_url="", redirect_uri="")
    svc = SsoService(db=None, config=config)
    assert svc.enabled is False


def test_sso_enabled_with_config():
    config = OidcConfig(
        client_id="test-id", client_secret="secret",
        discovery_url="http://idp/.well-known/openid-configuration",
        redirect_uri="http://localhost/callback",
    )
    svc = SsoService(db=None, config=config)
    assert svc.enabled is True


def test_get_authorization_url_requires_config():
    svc = SsoService(db=None, config=None)
    with pytest.raises(ValueError, match="not configured"):
        svc.get_authorization_url()


def test_sso_routes_registered(client):
    from app.api.v1.router import api_router
    routes = [r.path for r in api_router.routes]
    assert "/auth/sso/login" in routes
    assert "/auth/sso/callback" in routes
