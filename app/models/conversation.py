# app/models/conversation.py
import uuid
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, CheckConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.knowledge_base import KnowledgeBase
    from app.models.message import Message
    from app.models.model_usage_log import ModelUsageLog   # 移入 TYPE_CHECKING


class Conversation(BaseModel):
    """会话表，记录用户与系统的对话会话"""
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")  # 修正：添加括号
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    kb_id: Mapped[Optional[uuid.UUID]] = mapped_column(   # 类型改为 Optional
        UUID(as_uuid=True),
        ForeignKey("knowledge_bases.id", ondelete="SET NULL"),  # 修正表名
        nullable=True
    )
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mode: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,   # 修正：不加括号
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="conversations")
    knowledge_base: Mapped[Optional["KnowledgeBase"]] = relationship(
        "KnowledgeBase",
        back_populates="conversations"
    )
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )
    model_usage_logs: Mapped[List["ModelUsageLog"]] = relationship(
        "ModelUsageLog",
        back_populates="conversation"
    )

    __table_args__ = (
        CheckConstraint(
            "mode IN ('emotion', 'knowledge', 'mixed')",
            name="conversations_mode_check"
        ),
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, user_id={self.user_id}, mode={self.mode})>"