"""
工具节点 —— 情感关怀 + 天气查询 + 通用知识搜索
"""

import asyncio
import re
import time
from typing import Dict, Any, List, Callable, Optional

import httpx

from app.services.agent.state import AgentState
from app.services.mcp_client import get_weather_client
from app.utils.logger import logger

# =====================================================
# 并发控制
# =====================================================

TOOL_SEMAPHORE = asyncio.Semaphore(20)

# =====================================================
# 工具函数
# =====================================================

def tool_check_emergency_risk(user_input: str) -> str:
    """危机干预检测"""

    risk_keywords = [
        "自杀",
        "不想活了",
        "结束生命",
        "自残",
        "伤害自己",
        "绝望"
    ]

    found = [w for w in risk_keywords if w in user_input]

    if found:
        logger.warning("🚨 高危关键词: %s", found)

        return (
            "CRITICAL_ALERT: 检测到用户存在严重情绪危机风险。\n"
            "请立即切换到危机干预模式。"
        )

    return "SAFE"


# =====================================================
# MCP 天气工具
# =====================================================

async def tool_get_weather(
        city: Optional[str]
):

    if not city:

        return (
            "请告诉我需要查询的城市，例如：\n"
            "北京天气如何？\n"
            "上海会下雨吗？"
        )

    client = get_weather_client()

    if client is None:
        return "天气服务不可用"

    return await client.call_tool(
        "get_current_weather",
        {
            "city": city
        }
    )


# =====================================================
# 心理工具
# =====================================================

def tool_suggest_relaxation_technique(
        stress_level: str
) -> str:

    techniques = {
        "高": "4-7-8 呼吸法：吸气4秒、屏息7秒、呼气8秒。",
        "中": "5-4-3-2-1 着陆练习。",
        "低": "喝杯温水并进行简单拉伸。"
    }

    return techniques.get(
        stress_level,
        "深呼吸三次。"
    )


# =====================================================
# 知识工具
# =====================================================

def tool_search_wiki_knowledge(
        query: str
) -> str:

    logger.info(
        "百科查询: %s",
        query
    )

    return f"关于【{query}】的常见解释..."


# =====================================================
# URL工具
# =====================================================

async def tool_fetch_url(url: str) -> str:

    ALLOWED_DOMAINS = {
        "v1.hitokoto.cn",
        "api.github.com"
    }

    parsed = __import__(
        "urllib.parse"
    ).urlparse(url)

    hostname = parsed.hostname

    if not hostname:
        return "URL无效"

    if hostname not in ALLOWED_DOMAINS:
        return f"禁止访问域名: {hostname}"

    async with httpx.AsyncClient(
            timeout=15
    ) as client:

        resp = await client.get(
            url,
            follow_redirects=True
        )

        resp.raise_for_status()

        return resp.text[:2000]


# =====================================================
# 注册表
# =====================================================

TOOL_REGISTRY: List[tuple] = [

    (
        ["天气", "气温", "下雨", "温度"],
        tool_get_weather,
        "city"
    ),

    (
        ["焦虑", "压力", "放松", "减压"],
        tool_suggest_relaxation_technique,
        "stress_level"
    ),

    (
        ["什么是", "为什么", "解释"],
        tool_search_wiki_knowledge,
        "query"
    ),

    (
        ["http://", "https://"],
        tool_fetch_url,
        "url"
    )
]

# =====================================================
# 城市识别
# =====================================================

COMMON_CITIES = [
    "北京",
    "上海",
    "广州",
    "深圳",
    "成都",
    "杭州",
    "武汉",
    "南京",
    "西安"
]


def extract_city(
        query: str
) -> Optional[str]:

    for city in COMMON_CITIES:

        if city in query:
            return city

    match = re.search(
        r"([\u4e00-\u9fa5]{2,10})(?:市|区|县)?",
        query
    )

    if match:

        candidate = match.group(1)

        noise_words = [
            "天气",
            "气温",
            "温度",
            "下雨",
            "怎么样",
            "如何",
            "会不会",
            "今天",
            "明天",
        ]

        for word in noise_words:
            candidate = candidate.replace(
                word,
                ""
            )

        candidate = candidate.strip()

        if len(candidate) >= 2:
            return candidate

    return None


# =====================================================
# 参数处理
# =====================================================

def prepare_param(
        param_key: str,
        query: str
) -> Any:

    if param_key in (
            "query",
            "url"
    ):
        return query

    if param_key == "stress_level":

        if "非常" in query:
            return "高"

        if "有点" in query:
            return "低"

        return "中"

    if param_key == "city":

        city = extract_city(query)

        if city:
            return city

        return None

    return query


# =====================================================
# 执行工具
# =====================================================

async def run_tool(
        func: Callable,
        param: Any
):

    start = time.time()

    try:

        if asyncio.iscoroutinefunction(func):

            result = await asyncio.wait_for(
                func(param),
                timeout=15
            )

        else:

            result = await asyncio.to_thread(
                func,
                param
            )

        logger.info(
            "工具 %s 执行成功 %.2fs",
            func.__name__,
            time.time() - start
        )

        return result

    except Exception as e:

        logger.error(
            "工具 %s 执行失败: %s",
            func.__name__,
            e
        )

        raise


# =====================================================
# 显式 MCP Tool Call
# =====================================================

async def _execute_tool_calls(
        tool_calls: list
) -> list:

    results = []

    client = get_weather_client()

    for tc in tool_calls:

        name = tc.get("name")

        args = tc.get(
            "arguments",
            {}
        )

        try:

            if (
                    name == "get_current_weather"
                    and client
            ):

                result = await client.call_tool(
                    name,
                    args
                )

                results.append(result)

            else:

                results.append(
                    f"工具 {name} 未实现"
                )

        except Exception as e:

            logger.error(
                "工具调用失败: %s",
                e
            )

            results.append(
                f"工具 {name} 执行失败"
            )

    return results


# =====================================================
# 主节点
# =====================================================

async def tools_node(
        state: AgentState
) -> Dict[str, Any]:

    async with TOOL_SEMAPHORE:

        tool_calls = state.get(
            "tool_calls",
            []
        )

        # MCP显式工具调用
        if tool_calls:

            results = await _execute_tool_calls(
                tool_calls
            )

            return {
                "tool_result": "\n".join(results)
            }

        query = state.get(
            "query",
            ""
        ).strip()

        if not query:

            return {
                "tool_result": "无输入"
            }

        # 危机检测永远优先
        if any(
                x in query
                for x in [
                    "自杀",
                    "自残",
                    "绝望",
                    "结束生命"
                ]
        ):

            return {
                "tool_result":
                    tool_check_emergency_risk(query)
            }

        # ==========================
        # 收集所有命中的工具
        # ==========================

        tasks = []

        matched_tools = []

        for (
                keywords,
                tool_func,
                param_key
        ) in TOOL_REGISTRY:

            if any(
                    kw in query
                    for kw in keywords
            ):

                param = prepare_param(
                    param_key,
                    query
                )

                matched_tools.append(
                    tool_func.__name__
                )

                tasks.append(
                    run_tool(
                        tool_func,
                        param
                    )
                )

        # 没有命中任何工具
        if not tasks:

            return {
                "tool_result":
                    "未匹配到合适工具"
            }

        logger.info(
            "命中工具: %s",
            matched_tools
        )

        # ==========================
        # 并发执行
        # ==========================

        results = await asyncio.gather(
            *tasks,
            return_exceptions=True
        )

        final_results = []

        for idx, result in enumerate(results):

            tool_name = matched_tools[idx]

            if isinstance(
                    result,
                    Exception
            ):

                logger.error(
                    "%s 执行失败: %s",
                    tool_name,
                    result
                )

                final_results.append(
                    f"【{tool_name}】执行失败"
                )

            else:

                final_results.append(
                    f"【{tool_name}】\n{result}"
                )

        return {
            "tool_result":
                "\n\n".join(final_results)
        }