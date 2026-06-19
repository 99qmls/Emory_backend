# app/services/emotion/analyzer.py
"""
情感分析核心逻辑——适配优化后的模板，解析全量分析结果。

返回 EmoAnalysis 数据类，包含：
  - is_emotional, emotion, secondary_emotion, confidence
  - response_tone, user_style, mimic_level, factors
"""

import json
import re

from typing import Optional, Tuple, List
from dataclasses import dataclass, field

from app.services.llm.factory import get_llm
from app.services.emotion.templates import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.utils.logger import logger


@dataclass
class EmoAnalysis:
    """情感分析完整结果"""
    # 情感存在性开关
    is_emotional: bool = False
    # 主情感标签
    emotion: str = "neutral"
    # 次要情感标签（混合情绪场景）
    secondary_emotion: Optional[str] = None
    # 分析结果的可信度
    confidence: float = 0.0
    # 直接指导回复生成的语气策略 将情感分析结果转化为行动指令
    response_tone: str = "polite"
    # 捕捉语言风格特征以优化回复适配性
    user_style: str = "平稳叙述"
    # 量化「风格同步」的强度（0.0=完全不模仿，1.0=高度模仿
    mimic_level: float = 0.0
    # 情绪的外部诱因列表
    factors: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "is_emotional": self.is_emotional,
            "emotion": self.emotion,
            "secondary": self.secondary_emotion,
            "confidence": self.confidence,
            "response_tone": self.response_tone,
            "user_style": self.user_style,
            "mimic_level": self.mimic_level,
            "factors": self.factors,
        }

class EmotionAnalyzer:
    def __init__(self, model_name: Optional[str] = None):
        self.llm = get_llm(model_name)
        self.temperature = 0.1

    async def analyze(self, text: str) -> EmoAnalysis:
        prompt = USER_PROMPT_TEMPLATE.format(text=text)
        raw_output = ""

        try:
            return self._parse_full_response(raw_output)
        except Exception as e:
            logger.error(f"情感分析失败：{e}, raw_output:{raw_output}")
            return EmoAnalysis()

    def _parse_full_response(self, text: str) -> EmoAnalysis:
        """解析 LLM 输出的 JSON，容错处理"""
        data = None
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r'\{[^{}]*\}', text)
            if match:
                try:
                    data = json.loads(match.group())
                except json.JSONDecodeError:
                    pass

        if data is None:
            logger.warning(f"情感分析 JSON 解析失败，原始输出: {text[:100]}")
            return EmoAnalysis()

    def _validate_and_build(self, data: dict) -> EmoAnalysis:
        """校验字段并构造 EmoAnalysis 实例"""
        is_emotional = bool(data.get("is_emotional", False))
        confidence = self._clamp_float(data.get("confidence", 0.0))

        #  情感标签
        valid_emotions = {
            "joy", "sadness", "anger", "fear", "surprise", "disgust",
            "anxiety", "gratitude", "embarrassment", "confusion",
            "anticipation", "loneliness", "jealousy", "pride",
            "relief", "boredom", "neutral"
        }
        emotion = data.get("emotion", "neutral")
        if emotion not in valid_emotions:
            emotion = "neutral"

        secondary = data.get("secondary")
        if secondary and secondary not in valid_emotions:
            secondary = None

            # 语气
        valid_tones = {
                "empathetic", "calm", "encouraging", "professional",
                "enthusiastic", "humorous", "warm", "playful",
                "clear", "patient", "polite"
            }
        tone = data.get("response_tone", "polite")
        if tone not in valid_tones:
            tone = "polite"

            # 风格与模仿度
            user_style = data.get("user_style", "平稳叙述")
            mimic_level = self._clamp_float(data.get("mimic_level", 0.0))

            #  因素列表
            factors = data.get("factors", [])
            if not isinstance(factors, list):
                factors = []
            # 可选：校验每个 factor 包含 "factor" 和 "confidence"
            cleaned_factors = []
            for f in factors:
                if isinstance(f, dict) and "factor" in f:
                    factor_conf = self._clamp_float(f.get("confidence", 0.5))
                    cleaned_factors.append({
                        "factor": f["factor"],
                        "confidence": factor_conf
                    })
            factors = cleaned_factors

            return EmoAnalysis(
                is_emotional=is_emotional,
                emotion=emotion,
                secondary_emotion=secondary,
                confidence=confidence,
                response_tone=tone,
                user_style=user_style,
                mimic_level=mimic_level,
                factors=factors,
            )




    @staticmethod
    def _clamp_float(value, default=0.0) -> float:
        try:
            val = float(value)
            return max(0.0, min(1.0, val))
        except (TypeError, ValueError):
            return default


