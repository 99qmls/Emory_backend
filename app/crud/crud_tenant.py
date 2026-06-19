# app/crud/crud_tenant.py
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.tenant import Tenant
from app.schemas.tenant import TenantCreate, TenantUpdate


class CRUDTenant(CRUDBase[Tenant, TenantCreate, TenantUpdate]):
    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[Tenant]:
        stmt = select(Tenant).where(Tenant.name == name)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


tenant_crud = CRUDTenant(Tenant)