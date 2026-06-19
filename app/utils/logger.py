# app/utils/logger.py
"""
统一日志配置（基于 loguru）
特点：
- 自动日志轮转（按天、大小）
- 开发环境彩色控制台输出
- 生产环境可改为 JSON 格式写入文件
- 与标准 logging 兼容桥接
"""
import sys
from pathlib import Path
from loguru import logger

# 移除默认控制台输出
logger.remove()

# 日志保存目录
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# 控制台输出格式（开发环境彩色）
LOG_FORMAT_CONSOLE = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

# 文件输出格式（机器可读）
LOG_FORMAT_FILE = (
    "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
    "{name}:{function}:{line} - {message}"
)

# 通用日志配置
logger.add(
    sys.stdout,
    format=LOG_FORMAT_CONSOLE,
    level="DEBUG",
    colorize=True,
)

logger.add(
    LOG_DIR / "emory_{time:YYYY-MM-DD}.log",
    format=LOG_FORMAT_FILE,
    level="INFO",
    rotation="00:00",               # 每天午夜轮转
    retention="30 days",            # 保留30天
    compression="zip",              # 历史日志压缩
    encoding="utf-8",
)

# 错误日志单独存储
logger.add(
    LOG_DIR / "error_{time:YYYY-MM-DD}.log",
    format=LOG_FORMAT_FILE,
    level="ERROR",
    rotation="00:00",
    retention="90 days",
    compression="zip",
    encoding="utf-8",
)

__all__ = ["logger"]