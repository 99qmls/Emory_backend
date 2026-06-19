# app/crud/crud_conversation.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.base import CRUDBase
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.conversation import ConversationCreate, ConversationUpdate
from app.schemas.message import MessageCreate, MessageUpdate


class CRUDConversation(CRUDBase[Conversation, ConversationCreate, ConversationUpdate]):
    async def get_with_messages(
        self, db: AsyncSession, *, conv_id: UUID, user_id: Optional[UUID] = None
    ) -> Optional[Conversation]:
        stmt = select(Conversation).where(Conversation.id == conv_id, Conversation)
        if user_id:
            stmt = stmt.where(Conversation.user_id == user_id)
        stmt = stmt.options(selectinload(Conversation.messages))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi_by_user(
        self, db: AsyncSession, *, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id, Conversation)
            .order_by(desc(Conversation.updated_at))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def create_with_user(
        self, db: AsyncSession, *, obj_in: ConversationCreate, user_id: UUID
    ) -> Conversation:
        db_obj = Conversation(**obj_in.dict(), user_id=user_id)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


class CRUDMessage(CRUDBase[Message, MessageCreate, MessageUpdate]):
    async def get_multi_by_conversation(
        self, db: AsyncSession, *, conv_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conv_id, Message)
            .order_by(Message.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())


conversation_crud = CRUDConversation(Conversation)
message_crud = CRUDMessage(Message)