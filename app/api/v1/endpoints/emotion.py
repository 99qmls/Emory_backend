# app/api/v1/endpoints/emotion.py
import hashlib
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.api import deps
from app.core.database import get_db
from app.core.config import settings
from app.models.emotion_cache import EmotionAnalysisCache
from app.models.user import User
from pydantic import BaseModel, Field

from app.schemas.emotion import EmotionRequest, EmotionResponse

from sqlalchemy import func
from datetime import datetime, timedelta

router = APIRouter()


def get_text_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


@router.post("/analyze", response_model=EmotionResponse)
async def analyze_emotion(
        *,
        db: AsyncSession = Depends(get_db),
        req: EmotionRequest,
        current_user: User = Depends(deps.get_current_user),
) -> Any:
    """情感分析接口，优先使用缓存结果"""
    text_hash = get_text_hash(req.text)

    if not req.force_refresh:
        # 查询有效缓存
        stmt = select(EmotionAnalysisCache).where(
            and_(
                EmotionAnalysisCache.text_hash == text_hash,
                EmotionAnalysisCache.expires_at > func.now(),
                EmotionAnalysisCache
            )
        )
        result = await db.execute(stmt)
        cached = result.scalar_one_or_none()
        if cached:
            return EmotionResponse(
                text_hash=text_hash,
                emotion_tag=cached.emotion_tag,
                confidence=cached.confidence,
                from_cache=True
            )

    # 调用情感分析服务（这里用简化模拟，实际应调用 service/emotion/analyzer）
    try:
        from app.services.emotion.analyzer import analyze_text
        emotion_tag, confidence = await analyze_text(req.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"情感分析失败: {str(e)}")

    # 写入缓存
    cache_entry = EmotionAnalysisCache(
        text_hash=text_hash,
        emotion_tag=emotion_tag,
        confidence=confidence,
        # 使用相对时间设置
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(cache_entry)
    await db.commit()

    return EmotionResponse(
        text_hash=text_hash,
        emotion_tag=emotion_tag,
        confidence=confidence,
        from_cache=False
    )
