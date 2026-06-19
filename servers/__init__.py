"""
MCP Services Package
包含河南南阳天气服务等 MCP 微服务模块。
"""

# 1. 版本管理：便于追踪服务迭代
__version__ = "0.1.0"

# 2. 显式导出列表
# 当外部使用 `from mcp_services import *` 时，只会导入这里列出的内容

__all__ =[
    "__version__",
    "weather_server",

]
