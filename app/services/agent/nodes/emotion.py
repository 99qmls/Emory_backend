# app/services/agent/nodes/emotion.py
"""
情感分析节点 —— 动态加载情感标签（修复版）
"""

import json
import os
import re
from typing import Set, Dict, Any

from app.services.agent.state import AgentState
from app.services.llm.factory import get_llm
from app.utils.logger import logger

# ---------- 动态加载有效情感标签 ----------
_VALID_EMOTIONS: Set[str] = set()

def _load_valid_emotions() -> Set[str]:
    """从 emotion.txt 的第一行配置中解析有效标签"""
    prompt_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "prompts", "emotion.txt"
    )
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()        # 修复：使用 readline()
        match = re.match(r"^#EMOTION_LABELS:\s*(.*)$", first_line)
        if match:
            labels = match.group(1).split()
            logger.info(f"从 emotion.txt 加载情感标签 {len(labels)} 个")
            return set(labels)
    except Exception as e:
        logger.error(f"读取 emotion.txt 标签配置失败: {e}")

    logger.warning("使用降级情感标签集（中性, 危机）")
    return {"中性", "危机"}

_VALID_EMOTIONS = _load_valid_emotions()

# ---------- 加载提示词（跳过第一行） ----------
_EMOTION_SYSTEM_PROMPT: str = ""

def _load_system_prompt() -> str:
    prompt_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "prompts", "emotion.txt"
    )
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        # 去除第一行配置，拼接剩余内容
        return "".join(lines[1:]).strip()
    except Exception as e:
        logger.error(f"读取 emotion.txt 提示词失败: {e}")
        return ""

_EMOTION_SYSTEM_PROMPT = _load_system_prompt()

# ---------- 节点主逻辑 ----------
async def emotion_node(state: AgentState) -> Dict[str, Any]:
    """分析用户输入的情感，结果写入 state['emotion']"""
    if not _EMOTION_SYSTEM_PROMPT:
        logger.error("情感分析提示词为空，返回默认情感")
        return {"emotion": _default_emotion()}

    llm = get_llm()
    query = state.get("query", "")

    try:
        raw_output = await llm.generate(
            prompt=query,
            system_prompt=_EMOTION_SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=300,
        )
        json_str = _extract_json(raw_output)
        if not json_str:
            logger.warning(f"未能从输出中提取 JSON，原始: {raw_output[:100]}")
            return {"emotion": _default_emotion()}

        analysis = json.loads(json_str)
        validated = _validate_analysis(analysis)
        return {"emotion": validated}                # 修复：返回验证后的结果
    except Exception as e:
        logger.error(f"情感分析节点异常: {e}")
        return {"emotion": _default_emotion()}

# ---------- 辅助函数 ----------
def _extract_json(text: str) -> str:
    """从 LLM 输出中提取第一个 JSON 对象"""
    match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
    return match.group() if match else ""

def _validate_analysis(data: dict) -> dict:
    """校验并补全情感分析结果"""
    # 主导情绪
    dominant = data.get("dominant_emotion", "中性")
    if dominant not in _VALID_EMOTIONS:
        dominant = "中性"

    # 整体强度
    try:
        overall = max(1, min(10, int(data.get("overall_intensity", 1))))
    except (ValueError, TypeError):
        overall = 1

    # 情绪列表
    emotions = data.get("emotions", [])
    cleaned_emotions = []
    for e in emotions:
        if isinstance(e, dict):
            label = e.get("label", "中性")
            if label not in _VALID_EMOTIONS:
                continue
            try:
                intensity = max(0.0, min(1.0, float(e.get("intensity", 0.5))))
            except (ValueError, TypeError):
                intensity = 0.5
            cleaned_emotions.append({"label": label, "intensity": intensity})

    return {
        "dominant_emotion": dominant,
        "overall_intensity": overall,
        "emotions": cleaned_emotions,
        "suggested_tone": data.get("suggested_tone", "专业冷静"),
        "reasoning": data.get("reasoning", ""),
    }

def _default_emotion() -> dict:
    return {
        "dominant_emotion": "中性",
        "overall_intensity": 1,
        "emotions": [],
        "suggested_tone": "专业冷静",
        "reasoning": "系统默认值",
    }