from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Optional
from uuid import UUID
from datetime import datetime


class TokenPayload(BaseModel):
    """
    JWT 负载与令牌模型
    sub 用户id
    exp 验证jwt有效
    """
    sub: Optional[str] = None
    exp: Optional[str] = None


class Token(BaseModel):
    """
    access_token 字段：存储JWT 字符串
    token_type 标识令牌类型
   """
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    """
    登录与注册请求
    """
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """
    注册
    """
    username: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: Optional[str] = None
    tenant_id: Optional[str] = None
    tenant_name: Optional[str] = None
    role: str = "member"

    @model_validator(mode='after')
    def check_tenant(self) -> 'RegisterRequest':
        if not self.tenant_id and not self.tenant_name:
            raise ValueError('必须提供 tenant_id 或 tenant_name')
        return self

    """
    工具方法
    """

    def user_create_dict(self) -> dict:
        return {
            "username": self.username,
            "email": self.email,
            "password": self.password,
            "full_name": self.full_name,
            "role": self.role,
        }


class UserResponse(BaseModel):
    """
    请求响应
    """
    id: UUID
    tenant_id: UUID
    username: str
    email: str
    full_name: str | None = None
    role: str
    is_active: bool
    emotion_preference: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
