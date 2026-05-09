from app.core.config import Settings


def test_settings_have_enterprise_rag_defaults():
    settings = Settings()

    assert settings.app_name == "Enterprise RAG Knowledge Platform"
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.postgres_db == "enterprise_rag"
    assert settings.redis_url.startswith("redis://")


def test_default_jwt_secret_key_is_long_enough_for_hs256():
    settings = Settings()

    assert len(settings.jwt_secret_key.encode("utf-8")) >= 32


def test_settings_have_milvus_vector_store_defaults():
    settings = Settings()

    assert settings.milvus_uri == "http://milvus:19530"
    assert settings.milvus_token is None
    assert settings.milvus_collection == "enterprise_rag_chunks"
    assert settings.vector_dimension == 1536


def test_settings_have_s3_compatible_object_storage_defaults():
    settings = Settings()

    assert settings.object_storage_endpoint == "http://minio:9000"
    assert settings.object_storage_bucket == "enterprise-rag-documents"
    assert settings.object_storage_access_key == "minioadmin"
    assert settings.object_storage_secret_key == "minioadmin"
    assert settings.object_storage_region == "us-east-1"
