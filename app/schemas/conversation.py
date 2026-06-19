# app/schemas/conversation.py
from typing import Optional
from pydantic import BaseModel


class ConversationBase(BaseModel):
    title: Optional[str] = None
    mode: str


class ConversationCreate(ConversationBase):
    kb_id: Optional[str] = None


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    mode: Optional[str] = None
    kb_id: Optional[str] = None


class ConversationInDBBase(ConversationBase):
    id: str
    user_id: str
    kb_id: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True