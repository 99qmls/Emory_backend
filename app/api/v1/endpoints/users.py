# app/api/v1/endpoints/users.py
from typing import Any, List, Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.database import get_db
from app.crud.crud_user import user_crud
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, UserCreate

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def read_current_user(
    # current_user: User = Depends(deps.get_current_user),
    current_user: Annotated[User, Depends(deps.get_current_user)]
) -> Any:
    """获取自己的信息"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """更新自己的信息（不能修改角色和租户）"""
    # 防止越权修改角色
    if user_in.role is not None and user_in.role != current_user.role:
        raise HTTPException(status_code=403, detail="不能修改自己的角色")
    user = await user_crud.update(db, db_obj=current_user, obj_in=user_in)
    return user


@router.get("/", response_model=List[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    tenant_id: UUID = Depends(deps.get_current_tenant_id),
    _: User = Depends(deps.get_current_admin_user),   # 需要管理员权限
) -> Any:
    """获取当前租户下的所有用户"""
    users = await user_crud.get_multi_by_tenant(db, tenant_id=tenant_id, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(deps.get_current_tenant_id),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """获取指定用户详情（同一租户内）"""
    user = await user_crud.get(db, id=user_id)
    if not user or user.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="用户不存在")
    # 普通成员只能看自己
    if current_user.role not in ("admin", "superadmin") and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="权限不足")
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: UUID,
    user_in: UserUpdate,
    tenant_id: UUID = Depends(deps.get_current_tenant_id),
    _: User = Depends(deps.get_current_superuser),    # 仅超管可修改他人
) -> Any:
    """修改指定用户（仅超管）"""
    user = await user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    # 允许跨租户更新（超管）
    user = await user_crud.update(db, db_obj=user, obj_in=user_in)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    *,
    db: AsyncSession = Depends(get_db),
    user_id: UUID,
    _: User = Depends(deps.get_current_superuser),
) -> None:
    """软删除用户（超管）"""
    user = await user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    await user_crud.delete(db, id=user_id)