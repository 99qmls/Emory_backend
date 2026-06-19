# app/schemas/document.py
from typing import Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class DocumentBase(BaseModel):
    file_name: str
    file_url: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    status: str = "pending"
    chunk_count: int = 0
    error_message: Optional[str] = None


class DocumentCreate(DocumentBase):
    kb_id: str


class DocumentUpdate(BaseModel):
    file_name: Optional[str] = None
    status: Optional[str] = None
    chunk_count: Optional[int] = None
    error_message: Optional[str] = None


class DocumentInDBBase(DocumentBase):
    id: str
    kb_id: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """
    文档响应
    """
    id: UUID
    kb: UUID
    file_name: str
    file_url: str
    file_type: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        model_config = {
            "from_attributes": True,
            "json_schema_extra": {"example": {"username": "test"}}
        }
        # orm_mode = True
        # schema_extra = {
        #     "example": {
        #         "id": "550e8400-e29b-41d4-a716-446655440000",
        #         "kb_id": "550e8400-e29b-41d4-a716-446655440001",
        #         "file_name": "example.pdf",
        #         "file_url": "tenant_550e8400-e29b-41d4-a716-446655440000/kb_550e8400-e29b-41d4-a716-446655440001"
        #                     "/example.pdf",
        #         "file_type": "application/pdf",
        #         "status": "pending",
        #         "created_at": "2023-01-01T12:00:00Z",
        #         "updated_at": "2023-01-01T12:05:00Z"
        #     }
        # }
