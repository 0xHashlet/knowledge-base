from app.core.config import Settings


def test_settings_have_enterprise_rag_defaults():
    settings = Settings()

    assert settings.app_name == "Enterprise RAG Knowledge Platform"
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.postgres_db == "enterprise_rag"
    assert settings.redis_url.startswith("redis://")
