# 做统一分页处理
from typing import Optional, Any
from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """
    通用分页参数（可在端点中直接继承）
    skip 跳过记录数量
    limit 默认20 最大100数量
    """
    skip: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=100)


class ResponseWrapper(BaseModel):
    """
    统一响应
    """
    success: bool = True
    message: str = "ok"
    data: Optional[Any] = None
