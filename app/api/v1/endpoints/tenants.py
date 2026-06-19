# app/api/v1/endpoints/tenants.py
from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.database import get_db
from app.crud.crud_tenant import tenant_crud
from app.models.user import User
from app.schemas.tenant import TenantCreate, TenantUpdate, TenantResponse

router = APIRouter()


@router.get("/", response_model=List[TenantResponse])
async def list_tenants(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    _: User = Depends(deps.get_current_superuser),
) -> Any:
    """获取所有租户（超管）"""
    tenants = await tenant_crud.get_multi_all(db, skip=skip, limit=limit)
    return tenants


@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    *,
    db: AsyncSession = Depends(get_db),
    tenant_in: TenantCreate,
    _: User = Depends(deps.get_current_superuser),
) -> Any:
    """创建新租户（超管）"""
    existing = await tenant_crud.get_by_name(db, name=tenant_in.name)
    if existing:
        raise HTTPException(status_code=400, detail="租户名称已存在")
    tenant = await tenant_crud.create(db, obj_in=tenant_in)
    return tenant


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(deps.get_current_superuser),
) -> Any:
    """获取租户详情（超管）"""
    tenant = await tenant_crud.get(db, id=tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    return tenant


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    *,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID,
    tenant_in: TenantUpdate,
    _: User = Depends(deps.get_current_superuser),
) -> Any:
    """更新租户信息（超管）"""
    tenant = await tenant_crud.get(db, id=tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    tenant = await tenant_crud.update(db, db_obj=tenant, obj_in=tenant_in)
    return tenant


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    *,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID,
    _: User = Depends(deps.get_current_superuser),
) -> None:
    """软删除租户（超管）"""
    tenant = await tenant_crud.get(db, id=tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    await tenant_crud.delete(db, id=tenant_id)