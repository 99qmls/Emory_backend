# app/schemas/tenant.py
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID


class TenantBase(BaseModel):
    name: str = Field(max_length=255)
    description: Optional[str] = None
    status: str = "active"
    plan: str = "free"


class TenantCreate(TenantBase):
    name: str
    plan: Optional[str] = "free"
    pass


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    plan: Optional[str] = None


class TenantResponse(TenantBase):
    id: UUID
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}