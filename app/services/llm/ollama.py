"""
本地 Ollama 模型适配器 —— 实现 BaseLLM 接口，支持流式生成与 token 估算。
"""
import logging
import os
from typing import AsyncGenerator, Optional, Any

try:
    import ollama
except ImportError:
    raise ImportError("ollama未安装，执行 pip install ollama")

from app.services.llm.base import BaseLLM

logger = logging.getLogger(__name__)


class OllamaLLM(BaseLLM):
    _MODEL_LOAD_STATUS = {}

    def __init__(
            self,
            model: Optional[str] = None,
            host: Optional[str] = None,
            timeout: float = 120.0,
            max_input_length: int = 8000
    ):
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.timeout = timeout
        self.max_input_length = max_input_length
        self.model = model or self._get_default_model()

        if self.model not in self._MODEL_LOAD_STATUS:
            try:
                ollama.show(self.model)
                self._MODEL_LOAD_STATUS[self.model] = True
            except Exception as e:
                logger.warning(f"模型 {self.model} 加载检查失败: {e}")

    @staticmethod
    def _get_default_model() -> str:
        model = os.getenv("DEFAULT_LLM_MODEL", "deepseek-r1:7b")
        return model.replace("ollama:", "") if model.startswith("ollama:") else model

    def _get_client(self) -> ollama.AsyncClient:
        return ollama.AsyncClient(host=self.host, timeout=self.timeout)

    async def agenerate(
            self,
            prompt: str,
            system_prompt: Optional[str] = None,
            temperature: float = 0.7,
            max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        actual_model = self.model
        full_prompt = self._build_full_prompt(prompt, system_prompt)

        # 显存防护
        if "7b" in actual_model.lower() and len(full_prompt) > self.max_input_length:
            warn_msg = "\n[WARNING: 输入已截断]"
            available = max(0, self.max_input_length - len(warn_msg))
            full_prompt = full_prompt[:available] + warn_msg
            logger.warning(f"显存防护: {actual_model}, 截断至 {len(full_prompt)} 字符")

        options = {
            "temperature": temperature,
            "num_predict": max_tokens
        }

        try:
            client = self._get_client()
            # 正确调用方式：await 得到异步生成器，再迭代
            generator = await client.generate(
                model=actual_model,
                prompt=full_prompt,
                options=options,
                stream=True,
            )
            async for part in generator:
                yield part.get('response', '')
        except Exception as e:
            error_msg = f"ollama 错误 {type(e).__name__}: {str(e)[:200]}"
            logger.error(error_msg)
            yield error_msg

    async def generate(
            self,
            prompt: str,
            system_prompt: Optional[str] = None,
            temperature: float = 0.7,
            max_tokens: int = 2048,
            **kwargs
    ) -> str:
        """非流式生成：聚合所有流式片段并返回完整回复"""
        chunks = []
        async for chunk in self.agenerate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        ):
            chunks.append(chunk)
        return "".join(chunks)

    def _build_full_prompt(self, prompt: str, system_prompt: Optional[str]) -> str:
        if not system_prompt:
            return prompt
        return f"【系统指令】{system_prompt}\n\n用户：{prompt}\n\n助手："