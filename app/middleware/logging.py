# app/middleware/logging.py
"""
请求/响应日志中间件
记录每个 HTTP 请求的方法、路径、状态码、处理耗时
"""
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.logger import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        # 记录请求信息
        logger.info(f"--> {request.method} {request.url.path} 客户端: {request.client.host}")

        response = await call_next(request)

        process_time = time.time() - start_time
        # 记录响应信息
        logger.info(
            f"<-- {request.method} {request.url.path} "
            f"状态码: {response.status_code} "
            f"耗时: {process_time:.3f}s"
        )
        # 可添加自定义响应头
        response.headers["X-Process-Time"] = str(process_time)
        return response
