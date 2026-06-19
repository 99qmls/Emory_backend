# app/services/llm/base.py
"""
LLM 抽象基类 — 遵循最小抽象原则，子类只需实现核心流式接口即可工作。
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional


class BaseLLM(ABC):
    """大语言模型统一接口

       设计原则：
           - 子类必须实现异步流式生成 `agenerate`。
           - `generate` 提供默认实现（拼接流式结果），子类可覆盖以提升性能。
           - `get_num_tokens` 提供基于字符数的粗略估算，子类可覆盖以提供精确计数。
       """

    @abstractmethod
    async def agenerate(
            self,
            prompt: str,
            system_prompt: Optional[str] = None,
            temperature: float = 0.7,
            max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """异步流式生成文本（必须实现）"""
        ...

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """非流式生成完整回答，默认通过拼接 `agenerate` 实现。"""
        parts: list[str] = []
        async for chunk in self.agenerate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            parts.append(chunk)
        return "".join(parts)

    def get_num_tokens(self, text: str) -> int:
        """估算 token 数量，默认按字符数/4 粗略计算。子类可覆盖实现精确 tokenizer。"""
        return len(text)//3
