from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    username: str = Field(min_length=2, max_length=100)
    email: EmailStr
    full_name: Optional[str] = None
    role: str = "member"

class UserCreate(UserBase):
    password: str = Field(min_length=6)
    tenant_id: Optional[UUID] = None

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    emotion_preference: Optional[dict] = None

class UserResponse(BaseModel):
    id: UUID                       # 不再是 str
    tenant_id: UUID                # 不再是 str
    username: str
    email: str                     # 响应不需要 EmailStr 验证
    full_name: Optional[str] = None
    role: str
    is_active: bool
    emotion_preference: Optional[dict] = None
    created_at: datetime           # 不再是 str
    updated_at: datetime           # 不再是 str

    model_config = {"from_attributes": True}