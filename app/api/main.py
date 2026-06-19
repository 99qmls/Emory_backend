# app/api/v1/main.py

from fastapi import APIRouter

# 【修正点】
# 确保 endpoints 文件夹下有一个 __init__.py 文件。
# 这里显式导入各个模块，以便 IDE 识别
from app.api.v1.endpoints import (
    auth,
    emotion,
    users,
    knowledge,
    chat,
    agent,
    admin,
    tenants
)

# 创建 v1 版本的主路由器
api_router = APIRouter()

# --- 注册子路由 ---

# 1. 情感分析 (你之前的截图重点)
api_router.include_router(
    emotion.router,
    prefix="/emotion",
    tags=["emotion"]
)

# 2. 认证与用户
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"]
)
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"]
)

# 3. 知识库与文档
api_router.include_router(
    knowledge.router,
    prefix="/knowledge",
    tags=["knowledge"]
)

# 4. 聊天与智能体
api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["chat"]
)
api_router.include_router(
    agent.router,
    prefix="/agent",
    tags=["agent"]
)

# 5. 系统与租户 (通常给管理员用)
api_router.include_router(
    tenants.router,
    prefix="/tenants",
    tags=["tenants"]
)
api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["admin"]
)