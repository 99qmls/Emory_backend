# app/models/knowledge_base.py
import uuid
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel
from app.models.tenant import Tenant

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.conversation import Conversation


class KnowledgeBase(BaseModel):
    """知识库表，属于某个租户，包含文档集合"""
    __tablename__ = "knowledge_bases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    embedding_model: Mapped[str] = mapped_column(
        String(100),
        default="m3e",
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # 关系
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="knowledge_bases")
    documents: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="knowledge_base",
        cascade="all, delete-orphan"
    )
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation",
        back_populates="knowledge_base"
    )

    def __repr__(self) -> str:
        return f"<KnowledgeBase(id={self.id}, name={self.name}, tenant_id={self.tenant_id})>"