import os
import re
import asyncio
from typing import Dict, Any

from app.services.agent.state import AgentState
from app.services.llm.factory import get_llm
from app.utils.logger import logger

# ---------- 加载提示词 ----------
_SUPERVISOR_PROMPT = None

def _load_supervisor_prompt() -> str:
    prompt_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "prompts", "supervisor.txt"
    )
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        logger.error(f"打开supervisor.txt错误：{e}")
        return ""

_SUPERVISOR_PROMPT = _load_supervisor_prompt()

# 允许的目标节点（与提示词保持一致）
_ALLOWED_TARGETS = {"retriever", "tools", "generator", "finish"}


def clean_llm_output(text: str) -> str:
    """
    清理 DeepSeek-R1 等推理模型输出的 <think> 标签，
    支持完整标签、未闭合标签、截断标签。
    """
    # 1. 移除完整的 <think>...</think> 块（含换行）
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    # 2. 移除未闭合的 <think> 及之后的所有内容（因为推理在标签内，路由词应在其后或之外）
    text = re.sub(r'<think>.*', '', text, flags=re.DOTALL)
    # 3. 清理可能残留的 </think>
    text = text.replace('</think>', '')
    return text.strip()


def extract_routing_target(text: str) -> str:
    """
    从清洗后的文本中提取路由目标，使用正则匹配允许的节点名。
    如果有多个匹配，取最后一个（通常离最终输出最近）。
    如果未找到任何允许的节点，返回空字符串。
    """
    # 大小写不敏感匹配完整单词
    matches = re.findall(r'\b(retriever|tools|generator|finish)\b', text, re.IGNORECASE)
    if matches:
        return matches[-1].lower()  # 取最后一个匹配
    # 如果没找到，尝试匹配可能被部分截断的单词（如 "genera" -> "generator"）
    # 可选，此处暂不实现，直接返回空
    return ""


async def supervisor_node(state: AgentState) -> Dict[str, Any]:
    """
    根据用户输入决定下一步节点
    """
    if not _SUPERVISOR_PROMPT:
        logger.error("supervisor提示为空")
        return {"next_node": "generator"}

    llm = get_llm()
    query = state.get("query", "")

    combined_prompt = (
        f"{_SUPERVISOR_PROMPT}\n\n"
        f"用户输入: {query}"
    )

    try:
        raw_output = await asyncio.wait_for(
            llm.generate(
                prompt=combined_prompt,
                temperature=0.1,
                max_tokens=20,  # 增大，避免截断路由词
            ),
            timeout=15.0
        )

        logger.info(f"Supervisor原始输出:\n{raw_output}")

        # 第一步：清洗 <think> 标签
        raw_output = clean_llm_output(raw_output)
        logger.info(f"Supervisor清洗后:\n{raw_output}")

        # 第二步：用正则提取路由目标，不再剔除非字母
        target = extract_routing_target(raw_output)

        # 第三步：兜底处理
        if not target or target not in _ALLOWED_TARGETS:
            logger.warning(f"非法路由输出: '{target}'，原始: {raw_output}")
            target = "generator"

        return {"next_node": target}

    except asyncio.TimeoutError:
        logger.error("Supervisor超时")
        return {"next_node": "generator"}
    except Exception as e:
        logger.error(f"Supervisor异常: {e}")
        return {"next_node": "generator"}