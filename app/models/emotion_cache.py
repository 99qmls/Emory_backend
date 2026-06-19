# app/models/emotion_cache.py
import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy import String, DateTime, Numeric, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel


class EmotionAnalysisCache(BaseModel):
    """情感分析缓存表，用于缓存文本的情感分析结果，减少重复调用"""
    is_deleted = None
    __tablename__ = "emotion_analysis_cache"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    text_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False
    )
    emotion_tag: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 2),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    def __repr__(self) -> str:
        return f"<EmotionAnalysisCache(id={self.id}, text_hash={self.text_hash[:8]}..., emotion={self.emotion_tag})>"