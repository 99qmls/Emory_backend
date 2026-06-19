from typing import Optional,Annotated
from uuid import UUID
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.crud.crud_user import user_crud
from app.models.user import User
# from app.schemas.auth import TokenPayload  # V2 兼容，可暂时不使用

# 流量密码认证
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db),
    # token: str = Depends(oauth2_scheme)
) -> User:
    """从JWT解析当前登录用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # print("前端传来的 token:", token)
    # print("验证密钥前5位:", settings.SECRET_KEY[:5])

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # 🔹 使用 payload.get 直接取 sub，避免 Pydantic V2 校验问题
        sub = payload.get("sub")
        if sub is None:
            print("⚠️ JWT payload 中 sub 缺失")
            raise credentials_exception

        # 🔹 可选：检查 token 是否过期
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            exp = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            now = datetime.now(timezone.utc)
            if exp < now:
                print(f"⚠️ Token 已过期: {exp}")
                raise credentials_exception

    except JWTError as e:
        print("❌ JWT decode 失败:", e)
        raise credentials_exception

    # 获取用户
    user = await user_crud.get(db, id=UUID(sub))
    if user is None or not user.is_active:
        raise HTTPException(status_code=403, detail="账户已禁用或不存在")
    return user


async def get_current_tenant_id(
    current_user: User = Depends(get_current_user)
) -> UUID:
    """提取租户ID"""
    return current_user.tenant_id


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """要求当前用户角色为 admin 或 superadmin"""
    if current_user.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """仅超级管理员可访问"""
    if current_user.role != "superadmin":
        raise HTTPException(status_code=403, detail="需要超级管理员权限")
    return current_user