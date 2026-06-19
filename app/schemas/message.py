# app/schemas/message.py
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class MessageBase(BaseModel):
    role: str
    content: str
    emotion_tag: Optional[str] = None
    emotion_confidence: Optional[float] = None
    token_count: Optional[int] = None
    model_name: Optional[str] = None


class MessageCreate(MessageBase):
    conversation_id: UUID


class MessageUpdate(BaseModel):
    content: Optional[str] = None
    emotion_tag: Optional[str] = None
    emotion_confidence: Optional[float] = None


class MessageInDBBase(MessageBase):
    id: str
    conversation_id: str
    created_at: str

    class Config:
        from_attributes = True