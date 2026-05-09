from fastapi import APIRouter

from app.api.v1 import auth, departments, documents, feedback, health, knowledge_bases, permissions, roles, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(departments.router)
api_router.include_router(roles.router)
api_router.include_router(permissions.router)
api_router.include_router(knowledge_bases.router)
api_router.include_router(documents.router)
api_router.include_router(feedback.router)
api_router.include_router(health.router, tags=["health"])
