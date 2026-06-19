# ==============================================
# app/core/exceptions.py
# 自定义异常 + 全局异常处理器注册
# ==============================================
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
import traceback

from app.utils.logger import logger


# -------------------- 自定义业务异常基类 --------------------
class BaseHTTPException(Exception):
    """带状态码和详情的业务异常基类"""

    def __init__(self, status_code: int, detail: str = ""):
        self.status_code = status_code
        self.detail = detail


# -------------------- 常见业务异常 --------------------
class TenantNotFoundError(BaseHTTPException):
    def __init__(self, detail: str = "租户不存在"):
        super().__init__(status_code=404, detail=detail)


class UserNotFoundError(BaseHTTPException):
    def __init__(self, detail: str = "用户不存在"):
        super().__init__(status_code=404, detail=detail)


class KnowledgeBaseNotFoundError(BaseHTTPException):
    def __init__(self, detail: str = "知识库不存在"):
        super().__init__(status_code=404, detail=detail)


class DocumentProcessingError(BaseHTTPException):
    def __init__(self, detail: str = "文档处理失败"):
        super().__init__(status_code=500, detail=detail)


# -------------------- 异常处理函数 --------------------
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning(f"HTTP异常 {exc.status_code}: {exc.detail}  路径: {request.url.path}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"请求验证失败: {exc.errors()}  路径: {request.url.path}")
    return JSONResponse(
        status_code=422,
        content={"detail": "请求参数验证失败", "errors": exc.errors()},
    )


async def base_http_exception_handler(request: Request, exc: BaseHTTPException):
    logger.error(f"业务异常 {exc.status_code}: {exc.detail}  路径: {request.url.path}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"数据库异常: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"detail": "内部数据库错误，请联系管理员"},
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.critical(f"未处理异常: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误，请联系管理员"},
    )


# -------------------- 注册函数 --------------------
def register_exception_handlers(app: FastAPI):
    """将上述异常处理器绑定到 FastAPI 实例"""
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(BaseHTTPException, base_http_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    # 兜底处理器必须最后注册
    app.add_exception_handler(Exception, unhandled_exception_handler)
