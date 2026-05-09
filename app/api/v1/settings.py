from fastapi import APIRouter, Depends

from app.api.deps import require_admin
from app.core.config import get_settings

router = APIRouter(prefix="/settings", tags=["settings"], dependencies=[Depends(require_admin)])


@router.get("")
def get_system_settings() -> dict:
    s = get_settings()
    return {
        "llm": {
            "endpoint": s.llm_endpoint,
            "model": s.llm_model,
            "temperature": s.llm_temperature,
            "max_tokens": s.llm_max_tokens,
            "system_prompt": s.llm_system_prompt,
        },
        "embedding": {
            "endpoint": s.embedding_endpoint,
            "model": s.embedding_model,
        },
        "rerank": {
            "endpoint": s.rerank_endpoint,
            "model": s.rerank_model,
            "top_k": s.rerank_top_k,
        },
        "milvus": {
            "uri": s.milvus_uri,
            "collection": s.milvus_collection,
            "dimension": s.vector_dimension,
        },
        "object_storage": {
            "endpoint": s.object_storage_endpoint,
            "bucket": s.object_storage_bucket,
            "region": s.object_storage_region,
        },
        "chat": {
            "history_ttl": s.chat_history_ttl,
        },
        "jwt": {
            "algorithm": s.jwt_algorithm,
            "expire_minutes": s.access_token_expire_minutes,
        },
    }
