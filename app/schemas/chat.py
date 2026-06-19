# app/schemas/chat.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Union, Dict, Any
from uuid import UUID


class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[UUID] = None
    kb_id: Optional[UUID] = None
    model: Optional[str] = None
    config: Optional[Dict[str, Any]]


class ConversationCreate(BaseModel):
    title: Optional[str] = None
    mode: str = "mixed"   # emotion / knowledge / mixed
    kb_id: Optional[UUID] = None


class MessageCreate(BaseModel):
    conversation_id: UUID
    role: str
    content: str
    emotion_tag: Optional[str] = None
    emotion_confidence: Optional[float] = None
    token_count: Optional[int] = None
    model_name: Optional[str] = None

    @field_validator("conversation_id", mode="before")
    def parse_uuid(cls, v):
        if isinstance(v, str):
            return UUID(v)
        return v


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    emotion_tag: Optional[str] = None
    emotion_confidence: Optional[float] = None
    token_count: Optional[int] = None
    model_name: Optional[str] = None
    created_at: str

    model_config = {"from_attributes": True}