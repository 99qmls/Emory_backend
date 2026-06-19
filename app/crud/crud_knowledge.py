# app/crud/crud_knowledge.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.knowledge_base import KnowledgeBase
from app.schemas.knowledge import KnowledgeBaseCreate, KnowledgeBaseUpdate


class CRUDKnowledgeBase(CRUDBase[KnowledgeBase, KnowledgeBaseCreate, KnowledgeBaseUpdate]):
    async def get_with_documents(
        self, db: AsyncSession, *, kb_id: UUID, tenant_id: Optional[UUID] = None
    ) -> Optional[KnowledgeBase]:
        stmt = select(KnowledgeBase).where(KnowledgeBase.id == kb_id, KnowledgeBase)
        if tenant_id:
            stmt = stmt.where(KnowledgeBase.tenant_id == tenant_id)
        stmt = stmt.options(selectinload(KnowledgeBase.documents))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi_by_tenant(
        self, db: AsyncSession, *, tenant_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[KnowledgeBase]:
        return await self.get_multi(db, skip=skip, limit=limit, filters={"tenant_id": tenant_id})

    async def create_with_tenant(
        self, db: AsyncSession, *, obj_in: KnowledgeBaseCreate, tenant_id: UUID
    ) -> KnowledgeBase:
        db_obj = KnowledgeBase(**obj_in.dict(), tenant_id=tenant_id)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


knowledge_crud = CRUDKnowledgeBase(KnowledgeBase)