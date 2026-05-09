from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Enterprise RAG Knowledge Platform"
    app_version: str = "0.1.0"
    environment: Literal["local", "test", "staging", "production"] = "local"
    api_v1_prefix: str = "/api/v1"
    cors_allowed_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_user: str = "rag"
    postgres_password: str = "rag_password"
    postgres_db: str = "enterprise_rag"
    database_url: str | None = None

    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None

    jwt_secret_key: str = Field(default="change-me-in-production-min-32-bytes", min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    milvus_uri: str = "http://milvus:19530"
    milvus_token: str | None = None
    milvus_collection: str = "enterprise_rag_chunks"
    vector_dimension: int = 1536

    object_storage_endpoint: str = "http://minio:9000"
    object_storage_bucket: str = "enterprise-rag-documents"
    object_storage_access_key: str = "minioadmin"
    object_storage_secret_key: str = "minioadmin"
    object_storage_region: str = "us-east-1"

    @computed_field
    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field
    @property
    def celery_broker(self) -> str:
        return self.celery_broker_url or self.redis_url

    @computed_field
    @property
    def celery_backend(self) -> str:
        return self.celery_result_backend or self.redis_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
