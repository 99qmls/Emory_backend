# app/schemas/emotion.py
from pydantic import BaseModel, Field
from typing import Optional


class EmotionRequest(BaseModel):
    """情感分析请求体"""
    text: str = Field(..., min_length=1, max_length=5000, description="待分析的文本")
    force_refresh: bool = Field(False, description="是否强制重新分析，忽略缓存")


class EmotionResponse(BaseModel):
    """情感分析响应体"""
    text_hash: str = Field(..., description="文本的 SHA256 哈希值，用于缓存去重")
    emotion_tag: Optional[str] = Field(None, description="情感标签，如 joy, sadness, anger 等")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="置信度 0~1")
    from_cache: bool = Field(..., description="结果是否来自缓存")

    model_config = {"from_attributes": True}