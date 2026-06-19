# app/middleware/tenant.py

import contextvars
from uuid import UUID
from typing import Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.logger import logger  # 假设有logger

# 定义上下文变量（默认值为 None）
_tenant_ctx: contextvars.ContextVar[Optional[UUID]] = contextvars.ContextVar("tenant_id", default=None)


def set_current_tenant_id(tenant_id: UUID):
    """设置当前请求的租户 ID（通常在 deps 中调用）"""
    _tenant_ctx.set(tenant_id)
    logger.debug(f"设置租户ID: {tenant_id}")


def get_current_tenant_id() -> Optional[UUID]:
    """获取当前请求的租户 ID，可能为 None（未认证或公共路由）"""
    return _tenant_ctx.get()


class TenantMiddleware(BaseHTTPMiddleware):
    """
    租户中间件
    1. 尝试从请求头 X-Tenant-ID 提取租户 ID（用于内部服务调用或调试）
    2. 如果无法提取，后续由认证依赖项（deps）在解析用户后设置
    """

    async def dispatch(self, request: Request, call_next):
        # 尝试从请求头获取（仅作为备用，实际业务不依赖此值）
        tenant_id_header = request.headers.get("X-Tenant-ID")
        if tenant_id_header:
            try:
                tenant_id = UUID(tenant_id_header)
                _tenant_ctx.set(tenant_id)
                logger.info(f"从请求头获取租户ID: {tenant_id}")
            except ValueError:
                logger.warning(f"无效的租户ID格式: {tenant_id_header}")
                pass  # 非法 UUID 忽略
        # 继续处理请求
        response = await call_next(request)
        # 请求结束后不清理上下文，因为 contextvars 自动按协程隔离，不会泄漏
        return response
