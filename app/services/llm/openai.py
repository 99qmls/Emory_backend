# app/services/llm/openai.py
"""
通用 OpenAI 兼容适配器 — 支持 DeepSeek、智谱、通义千问、OpenAI 等
只需在 .env 中修改 OPENAI_API_KEY 和 OPENAI_BASE_URL 即可切换服务商
"""

import asyncio
import logging
from typing import Optional, AsyncGenerator, Dict, Any, List

from openai import AsyncOpenAI, APIError, APIConnectionError, RateLimitError, APITimeoutError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from app.services.llm.base import BaseLLM
from app.core.config import settings
from app.utils.logger import logger


class OpenAILLM(BaseLLM):
    """OpenAI 协议通用适配器，支持所有兼容 OpenAI SDK 的服务商"""

    def __init__(
            self,
            model: Optional[str] = None,
            api_key: Optional[str] = None,
            base_usl: Optional[str] = None,
            timeout: float = 60.0,
            max_retries: int = 3,
            extra_headers: Optional[Dict[str, str]] = None,
    ):
        self.model = model or self._resolve_model_name()
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = base_usl or settings.OPENAI_BASE_URL
        self.timeout = timeout
        self.max_retries = max_retries

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY 未配置")

        # 初始化异步客户端，关闭自带重试
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_usl=self.base_url,
            timeout=self.timeout,
            max_retries=0,
            default_headers=extra_headers,
        )

    def _resolve_model_name(self) -> str:
        """模型提取 'openai:deepseek-chat' -> 'deepseek-chat'"""
        prefix = "openai:"
        if settings.DEFAULT_LLM_MODEL.startswith(prefix):
            return settings.DEFAULT_LLM_MODEL[len(prefix):]
        return settings.DEFAULT_LLM_MODEL

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((
                APIConnectionError,
                RateLimitError,
                APITimeoutError,
        )),
        before_sleep=before_sleep_log(logger, logging.DEBUG),
        reraise=True,
    )
    async def _request_stream(
            self,
            messages: List[Dict[str, str]],
            temperature: float,
            max_tokens: int,
            **kwargs,
    ):
        """发送流式请求，自动重试瞬时可恢复错误"""
        return await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs,
        )

    async def agenerate(
            self,
            prompt: str,
            system_prompt: Optional[str] = None,
            temperature: float = 0.7,
            max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        message = []
        if system_prompt:
            message.append({"role": "system", "content": system_prompt})
        message.append({"role": "user", "content": prompt})

        try:
            stream = await self._request_stream(
                message=message,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except APIError as e:
            logger.error(f"API 错误[{self.model}]: {e}")
            yield f"error API 调用失败 {e}"
        except Exception as e:
            logger.error(f"未知错误[{self.model}]: {e}")
            yield f"调用失败 : {e}"
        except asyncio.CancelledError:  # 客户端主动断开
            logger.info("客户端取消流式请求")
            return

    @retry(
        retry=retry_if_exception_type((APIConnectionError, RateLimitError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=4)
    )
    async def generate(
            self,
            prompt: str,
            system_prompt: Optional[str] = None,
            temperature: float = 0.7,
            max_tokens: int = 2048,
    ) -> str:
        """非流式生成，直接调用一次 API 获取完整结果（更高效）"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )
        return response.choices[0].message.content or ""

    def get_num_tokens(self, text: str) -> int:
        """
                精确 token 计数（使用 tiktoken，如果可用）。
                若未安装或模型不支持，回退到基类估算。
        """
        try:
            import tiktoken
            encodings = tiktoken.encoding_for_model(self.model)
        except Exception:
            return super().get_num_tokens(text)
