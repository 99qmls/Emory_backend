# services/utils/redis_client.py
"""
应用生命周期内只建立一次连接池
原子性与并发安全
 单一职责原则
"""
import redis.asyncio as redis
from typing import Optional

class AsyncRedisMemoryClient:
    _instance: Optional["AsyncRedisMemoryClient"] = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, redis_client: redis.Redis):
        self.client = redis_client
        self._merge_sha: Optional[str] = None

    async def _ensure_script_loaded(self):
        """懒加载 Lua 脚本 SHA"""
        if self._merge_sha is None:
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

        async def append_summary(self, user_id: str, content: str, max_len: int = 2000) -> str:
            """追加摘要并自动截断"""
            await self._ensure_script_loaded()
            key = f"memory:summary:{user_id}"
            # 使用 evalsha 执行，比 eval 更快（避免每次发送完整脚本）
            return await self.client.evalsha(self._merge_sha, 1, key, content, max_len)
