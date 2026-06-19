# app/models/model_usage_log.py
import uuid
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, DateTime, CheckConstraint, Numeric, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.user import User
    from app.models.conversation import Conversation
    from app.models.message import Message


class ModelUsageLog(BaseModel):
    """模型使用日志表，用于统计和计费审计"""
    is_deleted = None
    __tablename__ = "model_usage_logs"

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
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    conversation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True
    )
    message_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="SET NULL"),
        nullable=True
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    request_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cost: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 6),  # 最多 10 位数字，其中 6 位小数，适合 USD 计费
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    # 关系（只读，通常不需要反向关系）
    tenant: Mapped["Tenant"] = relationship("Tenant",back_populates="model_usage_logs")
    user: Mapped[Optional["User"]] = relationship("User")
    conversation: Mapped[Optional["Conversation"]] = relationship("Conversation")
    message: Mapped[Optional["Message"]] = relationship("Message")

    __table_args__ = (
        CheckConstraint(
            "request_type IN ('chat', 'embedding', 'emotion_analysis')",
            name="model_usage_logs_request_type_check"
        ),
    )

    def __repr__(self) -> str:
        return f"<ModelUsageLog(id={self.id}, tenant_id={self.tenant_id}, model={self.model_name}, type={self.request_type})>"