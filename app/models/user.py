# app/models/user.py
import uuid
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Boolean, ForeignKey, DateTime, CheckConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.tenant import Tenant
    from app.models.conversation import Conversation
    from app.models.model_usage_log import ModelUsageLog   # 移到这里


class User(BaseModel):
    """用户表，UUID 主键，包含情感偏好字段"""
    __tablename__ = "users"

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
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(50),
        default="member",
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    emotion_preference: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        server_default='{"style": "friendly", "humor": 0.5, "empathy": 0.8}'
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
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    model_usage_logs: Mapped[List["ModelUsageLog"]] = relationship(
        "ModelUsageLog",
        back_populates="user"
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'member')",
            name="users_role_check"
        ),
    )