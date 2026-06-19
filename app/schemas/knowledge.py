# app/schemas/knowledge.py
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(max_length=255)
    description: Optional[str] = None
    embedding_model: str = "m3e"


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    embedding_model: Optional[str] = None


class KnowledgeBaseResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str] = None
    embedding_model: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentCreate(BaseModel):
    kb_id: UUID
    file_name: str
    file_url: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    status: str = "pending"


class DocumentResponse(BaseModel):
    id: UUID
    kb_id: UUID
    file_name: str
    file_url: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    status: str
    chunk_count: int = 0
    error_message: Optional[str] = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}