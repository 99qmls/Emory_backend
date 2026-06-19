# app/utils/constants.py
"""
全局常量定义（错误码、业务限制等）
"""


# ---------- 自定义错误码 ----------
class ERROR_CODES:
    # 通用
    SUCCESS = 0
    UNKNOWN_ERROR = 9999

    # 认证相关 1xxx
    INVALID_CREDENTIALS = 1001
    TOKEN_EXPIRED = 1002
    PERMISSION_DENIED = 1003

    # 租户相关 2xxx
    TENANT_NOT_FOUND = 2001
    TENANT_ALREADY_EXISTS = 2002

    # 用户相关 3xxx
    USER_NOT_FOUND = 3001
    USER_ALREADY_EXISTS = 3002
    USER_DISABLED = 3003

    # 知识库相关 4xxx
    KB_NOT_FOUND = 4001
    DOCUMENT_UPLOAD_FAILED = 4002
    DOCUMENT_PROCESSING_FAILED = 4003

    # 对话相关 5xxx
    CONVERSATION_NOT_FOUND = 5001
    AGENT_EXECUTION_FAILED = 5002


# 默认分页大小
DEFAULT_PAGE_SIZE = 20

# 文件上传限制（字节）
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB

# 支持的文档格式
ALLOWED_DOCUMENT_TYPES = [
    "application/pdf",
    "text/plain",
    "text/markdown",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]
