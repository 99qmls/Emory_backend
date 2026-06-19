# 增强功能（超时检测、Trace ID），并重点实现了LLM 降级策略（有模型用模型，没模型用规则）
# agent/nodes/entry_node.py
# 入口：生成摘要

import uuid
import logging
from asyncio import wait_for
from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from app.services.llm.factory import get_llm

import asyncio
from anyio import current_time

from app.services.agent.state import AgentState
logger = logging.getLogger(__name__)

# --- 配置常量 ---
SESSION_TIMEOUT = timedelta(seconds=30)
SUMMARY_CHAR_THRESHOLD = 200


async def entry_node(state: AgentState) -> Dict[str, Any]:
    # 1. 安全获取 trace_id（不修改 state）
    trace_id = state.get('trace_id') or str(uuid.uuid4().hex[:8])

    # 2. 会话超时检测（关键：不修改 state！）
    last_active = state.get('last_active')
    now = datetime.now(timezone.utc)

    if last_active is None:
        logger.warning(f"[{trace_id}] Missing last_active, forcing reset")
        return {
            "next_node": "error_handler",
            "is_session_expired": True,
            "trace_id": trace_id  # 新生成的 trace_id 用于错误处理
        }

    # 修复时区问题
    if last_active.tzinfo is None:
        last_active = last_active.replace(tzinfo=timezone.utc)

    if last_active < now - SESSION_TIMEOUT:
        logger.info(f"[{trace_id}] Session expired")
        return {
            "next_node": "error_handler",
            "is_session_expired": True,
            "trace_id": trace_id
        }

    # 3. 摘要生成（不修改 state！）
    query = state.get("query", "").strip()
    input_summary = query

    if len(query) > SUMMARY_CHAR_THRESHOLD:
        try:
            # 正确获取 LLM 客户端实例（通过工厂方法）
            llm = get_llm(state["llm_config"])  # 依赖注入实现
            prompt = f"请将以下用户输入总结为一句简练的意图描述（50字以内）：\n{query}"
            response = await asyncio.wait_for(
                llm.ainvoke(prompt),
                timeout=2.0
            )
            input_summary = response.content.strip()[:50]  # 强制截断
        except Exception as e:
            logger.warning(f"[{trace_id}] LLM fallback: {str(e)}")  # 用 warning 而非 error
            input_summary = _generate_fallback_summary(query)  # 封装降级逻辑

    # 4. 仅返回新数据（绝不修改 state）
    return {
        "input_summary": input_summary,
        "trace_id": trace_id,  # 保持原始 trace_id
        "is_session_expired": False,
        "next_node": "supervisor"
    }

def _generate_fallback_summary(text: str) -> str:
    """安全的规则降级摘要（过滤空句+语义完整）"""
    sentences = [s for s in text.replace('\n', '。').split('。') if s.strip()]
    summary = "。".join(sentences[:2]) if sentences else text[:100].strip()
    return summary[:100] + "..." if len(summary) > 100 else summary

