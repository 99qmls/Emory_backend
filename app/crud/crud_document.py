# app/crud/crud_document.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentUpdate


class CRUDDocument(CRUDBase[Document, DocumentCreate, DocumentUpdate]):
    async def get_multi_by_kb(
        self, db: AsyncSession, *, kb_id: UUID, skip: int = 0, limit: int = 100, status: Optional[str] = None
    ) -> List[Document]:
        filters = {"kb_id": kb_id}
        if status:
            filters["status"] = status
        return await self.get_multi(db, skip=skip, limit=limit, filters=filters)

    async def update_status(
        self, db: AsyncSession, *, doc_id: UUID, status: str, error_message: Optional[str] = None
    ) -> Optional[Document]:
        doc = await self.get(db, id=doc_id)
        if doc:
            doc.status = status
            if error_message:
                doc.error_message = error_message
            db.add(doc)
            await db.commit()
            await db.refresh(doc)
        return doc


document_crud = CRUDDocument(Document)