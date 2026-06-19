# app/api/v1/endpoints/auth.py
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserCreate

from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.database import get_db
from app.crud.crud_tenant import tenant_crud
from app.crud.crud_user import user_crud
from app.models import User
from app.schemas.auth import LoginRequest, Token, RegisterRequest, UserResponse

router = APIRouter()


# @router.post("/login", response_model=Token)
# async def login(
#     db: AsyncSession = Depends(get_db),
#     form_data: OAuth2PasswordRequestForm = Depends()
# ) -> Any:
#     # # token test
#     # print("签发密钥前5位:", settings.SECRET_KEY[:5])
#     # """OAuth2 兼容登录，返回 JWT token"""
#     user = await user_crud.authenticate(db, email=form_data.username, password=form_data.password)
#     if not user:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")
#     if not user.is_active:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账户已禁用")
#
#     access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#     return {
#         "access_token": security.create_access_token(
#             data={"sub": str(user.id)}, expires_delta=access_token_expires
#         ),
#         "token_type": "bearer",
#     }
#
# @router.post("/login", response_model=Token)
# async def login(
#         req: LoginRequest,
#         db: AsyncSession = Depends(get_db)
# ) -> Any:
#     user = await user_crud.authenticate(
#         db,
#         email=req.email,
#         password=req.password
#     )
#
#     if not user:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")
#     if not user.is_active:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账户已禁用")
#
#     access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#     return {
#         "access_token": security.create_access_token(
#             data={"sub": str(user.id)}, expires_delta=access_token_expires
#         ),
#         "token_type": "bearer",
#     }

@router.post("/login", response_model=Token)
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),  # 1. 使用 Form 依赖
        db: AsyncSession = Depends(get_db)
) -> Any:
    # 2. 注意：OAuth2 标准字段是 username，你需要将其作为 email 传入
    user = await user_crud.authenticate(
        db,
        email=form_data.username,
        password=form_data.password
    )

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账户已禁用")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
        *,
        db: AsyncSession = Depends(get_db),
        req: RegisterRequest,
) -> Any:
    """注册新用户，若租户不存在则自动创建"""
    # 检查邮箱唯一性
    if await user_crud.get_by_email(db, email=req.email):
        raise HTTPException(status_code=400, detail="邮箱已注册")

    # 确定租户
    if req.tenant_id:
        tenant = await tenant_crud.get(db, id=req.tenant_id)
        if not tenant:
            raise HTTPException(status_code=400, detail="指定租户不存在")
        tenant_id = tenant.id
    elif req.tenant_name:
        tenant = await tenant_crud.get_by_name(db, name=req.tenant_name)
        if not tenant:
            from app.schemas.tenant import TenantCreate
            tenant = await tenant_crud.create(db, obj_in=TenantCreate(name=req.tenant_name))
        tenant_id = tenant.id
    else:
        raise HTTPException(status_code=400, detail="必须提供 tenant_id 或 tenant_name")

    user_in_data = req.user_create_dict()
    user_in_data["tenant_id"] = tenant_id
    user_in = UserCreate(**user_in_data)
    user = await user_crud.create(db, obj_in=user_in)
    return user


@router.post("/refresh", response_model=Token)
async def refresh_token(
        current_user: User = Depends(deps.get_current_user)
) -> Any:
    """刷新 token（需携带现有有效 token）"""
    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = security.create_access_token(data={"sub": str(current_user.id)}, expires_delta=expires)
    return {"access_token": token, "token_type": "bearer"}
