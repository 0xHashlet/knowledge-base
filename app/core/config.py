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
    vector_dimension: int = 1024

    embedding_endpoint: str = "http://localhost:8080/v1"
    embedding_model: str = "bge-large-zh-v1.5"
    embedding_api_key: str = ""

    llm_endpoint: str = "http://localhost:8001/v1"
    llm_model: str = "qwen2.5"
    llm_api_key: str = ""
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2048
    llm_system_prompt: str = (
        "你是一个企业知识库助手。请仅根据提供的文档内容回答问题。"
        "如果文档内容不足以回答问题，请明确告知用户。不要编造信息。"
    )

    chat_history_ttl: int = 3600

    rerank_endpoint: str = "http://localhost:8080/v1"
    rerank_model: str = "bge-reranker-v2-m3"
    rerank_api_key: str = ""
    rerank_top_k: int = 5

    smtp_host: str = ""
    smtp_port: int = 25
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = False
    smtp_sender: str = "noreply@enterprise-rag.local"

    oidc_client_id: str = ""
    oidc_client_secret: str = ""
    oidc_discovery_url: str = ""
    oidc_redirect_uri: str = "http://localhost:8000/api/v1/auth/sso/callback"

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
