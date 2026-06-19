"""
生成器节点 —— 综合检索结果、情绪与工具输出，生成最终回答
企业级优化：工具结果优先、智能截断、强化清理、按需注入
"""
import re
import os
import asyncio
from typing import Dict, Any, Optional

from app.services.agent.state import AgentState
from app.services.llm.factory import get_llm
from app.utils.logger import logger


# ---------- 配置 ----------
class GeneratorConfig:
    PROMPT_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "prompts", "generator.txt"
    )
    MAX_TOKENS = 2000
    TEMPERATURE = 0.7
    MAX_TOOL_RESULT_LENGTH = 2000
    DEFAULT_PROMPT = (
        "你是一个智能助手。请基于以下信息回答用户问题：\n\n"
        "用户问题: {query}\n"
        "情绪状态: {emotion}\n"
        "建议语气: {suggested_tone}\n\n"
        "知识库内容: {context}\n"
        "{tool_section}"
        "\n注意：当工具查询结果不为空时，你必须完全依据工具结果回答，忽略知识库。"
    )


# ---------- 内部辅助函数 ----------
_PROMPT_CACHE: Optional[str] = None

def _load_prompt_template() -> str:
    """惰性加载提示词模板"""
    global _PROMPT_CACHE
    if _PROMPT_CACHE is not None:
        return _PROMPT_CACHE
    try:
        with open(GeneratorConfig.PROMPT_PATH, "r", encoding="utf-8") as f:
            template = f.read().strip()
            logger.info("成功加载 generator 提示词模板")
            _PROMPT_CACHE = template
            return template
    except Exception as e:
        logger.warning(f"提示词模板加载失败: {e}，使用默认模板")
        return GeneratorConfig.DEFAULT_PROMPT


def _build_context(state: AgentState) -> Dict[str, str]:
    """从状态中提取并构建上下文变量"""
    query = state.get("query", "").strip() or "空"

    # 情感信息
    emotion_data = state.get("emotion") or {}
    if not isinstance(emotion_data, dict):
        emotion_data = {}
    dominant = emotion_data.get("dominant_emotion", "中性")
    intensity = emotion_data.get("overall_intensity", 1)
    emotion_text = f"{dominant} (强度 {intensity}/10)"
    suggested_tone = emotion_data.get("suggested_tone", "专业冷静")

    # 知识库检索结果
    docs = state.get("retrieved_docs", [])
    context = "\n---\n".join(d.get("page_content", "") for d in docs) if docs else "无知识库检索结果"

    # 工具结果：截断保护，为空时不生成工具段落
    raw_tool = state.get("tool_result", "").strip()
    tool_section = ""
    if raw_tool:
        if len(raw_tool) > GeneratorConfig.MAX_TOOL_RESULT_LENGTH:
            raw_tool = raw_tool[:GeneratorConfig.MAX_TOOL_RESULT_LENGTH] + "\n...（结果已截断）"
        tool_section = f"工具查询结果（请优先使用）：\n{raw_tool}"

    return {
        "query": query,
        "emotion": emotion_text,
        "suggested_tone": suggested_tone,
        "context": context,
        "tool_section": tool_section,
        "tool_result": tool_section,
    }


def _clean_think_tags(text: str) -> str:
    """
    移除 DeepSeek 类模型的 <think> 推理链。
    处理完整标签和未闭合标签。
    """
    orig_len = len(text)
    # 1. 移除所有完整闭合的 <think>...</think>
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    # 2. 如果还有未闭合的 <think>，截断后续内容
    start_tag = cleaned.find('<think>')
    if start_tag != -1:
        logger.warning("检测到未闭合的 <think> 标签，将移除标签，保留后续内容")
        cleaned = cleaned[:start_tag] + cleaned[start_tag + len('<think>'):].strip()
    # 3. 清理残留的 </think> 标签
    cleaned = cleaned.replace('</think>', '').strip()
    logger.debug(f"思考标签清理：原长度={orig_len}，清理后={len(cleaned)}")
    return cleaned


# ---------- 节点入口函数 ----------
async def generator_node(state: AgentState) -> Dict[str, Any]:
    """
    综合上下文生成最终回答，并写入 final_answer。
    外层 asyncio.wait_for 提供整体超时保护。
    """
    try:
        # 构建上下文并渲染 prompt
        ctx = _build_context(state)
        template = _load_prompt_template()

        # 安全填充变量（缺失时降级为默认模板）
        try:
            prompt = template.format(**ctx)
        except KeyError as e:
            logger.warning(f"提示词变量缺失: {e}，使用默认模板")
            prompt = GeneratorConfig.DEFAULT_PROMPT.format(**ctx)

        # LLM 生成
        raw_answer = await asyncio.wait_for(
            get_llm().generate(
                prompt=prompt,
                temperature=GeneratorConfig.TEMPERATURE,
                max_tokens=GeneratorConfig.MAX_TOKENS,
            ),
            timeout=45.0
        )

        # 清理并返回
        final_answer = _clean_think_tags(raw_answer.strip() or "生成结果为空")
        return {"final_answer": final_answer}

    except asyncio.TimeoutError:
        logger.error("生成节点超时")
        return {"final_answer": "系统处理超时，请稍后重试。"}
    except Exception as e:
        logger.exception(f"生成节点异常: {e}")
        return {"final_answer": "系统内部错误，暂时无法回复。"}