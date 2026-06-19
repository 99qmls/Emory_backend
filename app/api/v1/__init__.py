# app/api/v1/__init__.py
from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, knowledge, chat, admin, tenants, agent, emotion

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["knowledge"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(agent.router, prefix="/agent", tags=["agent"])
api_router.include_router(emotion.router, prefix="/emotion", tags=["emotion"])