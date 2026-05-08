import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_permission_service
from app.models.knowledge_base import KnowledgeBase, KnowledgeBaseMember
from app.models.user import User
from app.schemas.knowledge_base import (
    KnowledgeBaseCreate,
    KnowledgeBaseMemberCreate,
    KnowledgeBaseMemberRead,
    KnowledgeBaseRead,
    KnowledgeBaseUpdate,
)
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])


@router.get("", response_model=list[KnowledgeBaseRead])
def list_knowledge_bases(
    offset: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service),
    db: Session = Depends(get_db),
) -> list[KnowledgeBase]:
    items = KnowledgeBaseService(db).list(offset=offset, limit=limit)
    accessible_ids = set(
        permission_service.filter_accessible_knowledge_base_ids(
            current_user,
            [item.id for item in items],
        )
    )
    return [item for item in items if item.id in accessible_ids]


@router.post("", response_model=KnowledgeBaseRead, status_code=status.HTTP_201_CREATED)
def create_knowledge_base(
    data: KnowledgeBaseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> KnowledgeBase:
    return KnowledgeBaseService(db).create(data, current_user)


@router.get("/{knowledge_base_id}", response_model=KnowledgeBaseRead)
def get_knowledge_base(
    knowledge_base_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service),
    db: Session = Depends(get_db),
) -> KnowledgeBase:
    if not permission_service.can_access_knowledge_base(current_user, knowledge_base_id):
        raise HTTPException(status_code=403, detail="Knowledge base access denied")
    knowledge_base = KnowledgeBaseService(db).get(knowledge_base_id)
    if knowledge_base is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return knowledge_base


@router.patch("/{knowledge_base_id}", response_model=KnowledgeBaseRead)
def update_knowledge_base(
    knowledge_base_id: uuid.UUID,
    data: KnowledgeBaseUpdate,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service),
    db: Session = Depends(get_db),
) -> KnowledgeBase:
    if not permission_service.can_manage_knowledge_base(current_user, knowledge_base_id):
        raise HTTPException(status_code=403, detail="Knowledge base management denied")
    service = KnowledgeBaseService(db)
    knowledge_base = service.get(knowledge_base_id)
    if knowledge_base is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return service.update(knowledge_base, data)


@router.delete("/{knowledge_base_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_base(
    knowledge_base_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service),
    db: Session = Depends(get_db),
) -> Response:
    if not permission_service.can_manage_knowledge_base(current_user, knowledge_base_id):
        raise HTTPException(status_code=403, detail="Knowledge base management denied")
    service = KnowledgeBaseService(db)
    knowledge_base = service.get(knowledge_base_id)
    if knowledge_base is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    service.delete(knowledge_base)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/{knowledge_base_id}/members",
    response_model=KnowledgeBaseMemberRead,
    status_code=status.HTTP_200_OK,
)
def grant_knowledge_base_member(
    knowledge_base_id: uuid.UUID,
    data: KnowledgeBaseMemberCreate,
    current_user: User = Depends(get_current_user),
    permission_service: PermissionService = Depends(get_permission_service),
    db: Session = Depends(get_db),
) -> KnowledgeBaseMember:
    if not permission_service.can_manage_knowledge_base(current_user, knowledge_base_id):
        raise HTTPException(status_code=403, detail="Knowledge base management denied")
    if KnowledgeBaseService(db).get(knowledge_base_id) is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return KnowledgeBaseService(db).grant_member(knowledge_base_id, data)

