# ======================================================
# jieba 预加载（必须放最顶部）
# ======================================================
import asyncio
import time
import logging
import sys
import os
from typing import Optional

import redis
from torch.nn.quantized._reference.modules import utils

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout
)

logger = logging.getLogger("app")

class JiebaDummy:
    def cut(self, text):
        return list(text)

logger.info("🚀 正在预加载 jieba 词典...")
start_time = time.time()

try:
    import jieba

    # 避免使用缓存目录问题
    jieba.dt.tmp_dir = None
    jieba.initialize()

    load_time = time.time() - start_time
    dict_path = jieba.get_dict_file().name

    logger.info("✅ jieba加载完成 %.2fs", load_time)
    logger.info("词典路径: %s", dict_path)

    _JIEBA_READY = True

except Exception:
    logger.exception("jieba初始化失败")
    jieba = JiebaDummy()
    load_time = 0.0
    _JIEBA_READY = False

from app.utils.redis_client import AsyncRedisMemoryClient

class AsyncRedisMemoryManager:
    """中期记忆纯逻辑管理器 —— 不负责创建连接，不保存配置"""

    def __init__(self, redis_client: redis.Redis):
        self.client = redis_client
        self._merge_sha: Optional[str] = None

    async def _ensure_script_loaded(self):
        if self._merge_sha is not None:
            return
        lua_script = """
        local key = KEYS[1]
        local new_line = ARGV[1]
        local max_len = tonumber(ARGV[2])
        local old = redis.call('GET', key) or ""
        local combined
        if old == "" then
            combined = new_line
        else
            combined = old .. "\\n" .. new_line
        end
        if string.len(combined) > max_len then
            combined = string.sub(combined, -max_len)
        end
        redis.call('SET', key, combined)
        return combined
        """
        self._merge_sha = await self.client.script_load(lua_script)

    async def append_summary(self, user_id: str, content: str, max_len: int = 300) -> str:
        """追加摘要并原子截断，返回合并后的完整字符串"""
        await self._ensure_script_loaded()
        key = f"memory:summary:{user_id}"
        return await self.client.evalsha(self._merge_sha, 1, key, content, max_len)

    async def get_summary(self, user_id: str) -> str:
        """读取中期记忆（纯文本）"""
        key = f"memory:summary:{user_id}"
        value = await self.client.get(key)
        return value or ""

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_manager:  AsyncRedisMemoryManager | None = None

# ======================================================
# FastAPI
# ======================================================

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 你自己的包
from app.api.v1 import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.services.mcp_client import (
    MCPWeatherClient,
    set_weather_client,
    get_weather_client
)


# ======================================================
# 生命周期管理
# ======================================================

@asynccontextmanager
async def lifespan(app):

    weather_client = None

    try:

        logger.info(
            "开始初始化天气MCP..."
        )

        weather_client = MCPWeatherClient(
            settings.MCP_WEATHER_URL
        )

        # await weather_client.initialize()
        await asyncio.wait_for(weather_client.initialize(), timeout=10.0)

        set_weather_client(
            weather_client
        )

        logger.info(
            "天气MCP初始化成功"
        )

    except Exception:

        logger.exception(
            "天气MCP初始化失败"
        )

        set_weather_client(
            None
        )

    yield

    if weather_client:

        await weather_client.close()


# ======================================================
# App Factory
# ======================================================

def create_app() -> FastAPI:
    app = FastAPI(
        title="Emory Backend API",
        description="Emotion AI Backend",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    register_exception_handlers(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    app.include_router(api_router, prefix="/api/v1")

    @app.get("/")
    async def root():
        return {
            "status": "running",
            "weather_service": "available" if get_weather_client() else "unavailable",
            "jieba_status": "ready" if _JIEBA_READY else "degraded",
            "jieba_load_time": f"{load_time:.2f}s"
        }

    return app


# ======================================================
# 实例化
# ======================================================

app = create_app()