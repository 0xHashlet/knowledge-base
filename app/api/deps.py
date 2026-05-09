from collections.abc import Generator
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models.user import User
from app.repositories.permission_repository import PermissionRepository
from app.repositories.users import UserRepository
from app.services.permission_service import PermissionService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_permission_service(db: Session = Depends(get_db)) -> PermissionService:
    return PermissionService(PermissionRepository(db))


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id = uuid.UUID(str(payload.get("sub")))
    except (TypeError, ValueError):
        raise credentials_error

    user = UserRepository(db).get_with_roles(user_id)
    if user is None or not user.is_active:
        raise credentials_error
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required",
        )
    return current_user


def require_knowledge_base_member(knowledge_base_id: uuid.UUID):
    def dependency(
        current_user: User = Depends(get_current_user),
        permission_service: PermissionService = Depends(get_permission_service),
    ) -> User:
        if not permission_service.can_access_knowledge_base(current_user, knowledge_base_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Knowledge base access denied",
            )
        return current_user

    return dependency


def get_redis():
    """Creates a Redis client from settings. Does not use Depends(get_db)."""
    import redis

    settings = get_settings()
    return redis.from_url(settings.redis_url, decode_responses=True)


def get_qa_service(
    db: Session = Depends(get_db),
    permission_service: PermissionService = Depends(get_permission_service),
):
    from app.repositories.chunks import ChunkRepository
    from app.services.embedding_service import create_embedding_service
    from app.services.llm_service import create_llm_service
    from app.services.qa_service import QaService
    from app.services.retrieval_service import RetrievalService
    from app.vectorstores.milvus import MilvusEmbeddingStore

    settings = get_settings()
    redis_client = get_redis()

    chunk_repo = ChunkRepository(db)
    milvus = MilvusEmbeddingStore(
        uri=settings.milvus_uri,
        token=settings.milvus_token,
        collection_name=settings.milvus_collection,
        dimension=settings.vector_dimension,
    )
    retrieval_svc = RetrievalService(
        chunk_repository=chunk_repo,
        embedding_store=milvus,
        permission_service=permission_service,
    )
    embedding_svc = create_embedding_service(
        settings.embedding_endpoint, settings.embedding_model
    )
    llm_svc = create_llm_service(
        endpoint=settings.llm_endpoint,
        model=settings.llm_model,
        system_prompt=settings.llm_system_prompt,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
    )
    return QaService(
        db=db,
        retrieval_service=retrieval_svc,
        llm_service=llm_svc,
        embedding_service=embedding_svc,
        redis_client=redis_client,
    )
