"""
城市坐标加载器 —— 支持从 JSON 文件、Redis、数据库等多种数据源灵活读取
"""
import json
import os
from typing import Dict, Tuple, Optional
from functools import lru_cache

from app.core.config import settings
from app.utils.logger import logger

# 默认配置文件路径（相对于本模块）
DEFAULT_CITY_COORDS_FILE = os.path.join(os.path.dirname(__file__), "city_coords.json")

# 全局可选缓存（避免频繁 I/O）
_city_coords_cache: Optional[Dict[str, Tuple[float, float]]] = None


def load_city_coords_from_file(filepath: str) -> Dict[str, Tuple[float, float]]:
    """从 JSON 文件加载城市坐标映射"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            raw: Dict[str, list] = json.load(f)
        # 转换 list -> tuple
        return {city: (float(lat), float(lon)) for city, (lat, lon) in raw.items()}
    except FileNotFoundError:
        logger.warning(f"城市坐标文件未找到: {filepath}，使用空映射")
        return {}
    except Exception as e:
        logger.error(f"加载城市坐标文件失败: {e}")
        return {}


# 可扩展：从 Redis / 数据库加载（示例接口）
async def load_city_coords_from_redis() -> Dict[str, Tuple[float, float]]:
    """预留：从 Redis 读取坐标（需 Redis 客户端）"""
    # from app.core.redis_client import redis
    # data = await redis.hgetall("city_coords")
    # return {k.decode(): tuple(map(float, v.decode().split(','))) for k, v in data.items()}
    return {}


def get_city_coords() -> Dict[str, Tuple[float, float]]:
    """
    获取城市坐标映射（带内存缓存）
    优先级：环境变量指定文件 > 默认 JSON 文件 > 空映射
    """
    global _city_coords_cache
    if _city_coords_cache is not None:
        return _city_coords_cache

    # 可通过 settings 指定配置文件路径，否则使用默认
    file_path = getattr(settings, "CITY_COORDS_FILE", DEFAULT_CITY_COORDS_FILE)
    coords = load_city_coords_from_file(file_path)

    # 如果有 Redis 或其他数据源，可在这里合并（例如：file 为基础，Redis 覆盖）
    # redis_coords = await load_city_coords_from_redis()
    # coords.update(redis_coords)

    _city_coords_cache = coords
    logger.info(f"城市坐标加载完成，共 {len(coords)} 个城市")
    return coords


def reload_city_coords():
    """手动刷新缓存（热加载）"""
    global _city_coords_cache
    _city_coords_cache = None
    get_city_coords()