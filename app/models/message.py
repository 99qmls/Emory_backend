# app/models/message.py
import uuid
from typing import Optional, TYPE_CHECKING, List
from datetime import datetime
from sqlalchemy import String, Text, Integer, ForeignKey, DateTime, CheckConstraint, Numeric, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.conversation import Conversation
    from app.models.model_usage_log import ModelUsageLog


class Message(BaseModel):
    """消息表，记录会话中的每条对话消息"""
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False
    )
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    emotion_tag: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    emotion_confidence: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 2),
        nullable=True
    )
    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    # 关系
    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="messages"
    )
    model_usage_logs: Mapped[List["ModelUsageLog"]] = relationship(
        "ModelUsageLog",
        back_populates="message"
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'assistant', 'system')",
            name="messages_role_check"
        ),
    )

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, role={self.role})>"