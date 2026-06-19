# app/models/tenant.py
import uuid
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, DateTime, CheckConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.knowledge_base import KnowledgeBase
    from app.models.model_usage_log import ModelUsageLog


class Tenant(BaseModel):
    """租户表，UUID 主键，增加 plan 字段"""
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        default="active",
        nullable=False
    )
    plan: Mapped[str] = mapped_column(
        String(50),
        default="free",
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
    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="tenant",
        cascade="all, delete-orphan"
    )
    knowledge_bases: Mapped[List["KnowledgeBase"]] = relationship(
        "KnowledgeBase",
        back_populates="tenant",
        cascade="all, delete-orphan"
    )
    model_usage_logs: Mapped[List["ModelUsageLog"]] = relationship(
        "ModelUsageLog",
        back_populates="tenant"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'suspended')",
            name="tenants_status_check"
        ),
        CheckConstraint(
            "plan IN ('free', 'pro', 'enterprise')",
            name="tenants_plan_check"
        ),
    )

    description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        default=None
    )