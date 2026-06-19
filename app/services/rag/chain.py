# app/services/rag/chain.py
"""
RAG 问答链 —— 优化版

- 自动集成混合检索器、LLM
- 支持对话历史、预设方案、自定义参数
- 适配最新 LangChain 文本分割器与检索器
- 异步流式与非流式双接口
"""

from typing import AsyncGenerator, Optional, List, Dict, Union
from dataclasses import dataclass

from app.services.rag.retriever import HybridRetriever
from app.services.llm.factory import get_llm
from app.services.llm.base import BaseLLM
from app.utils.logger import logger


@dataclass
class RAGConfig:
    """检索与生成参数集合"""
    top_k: int = 5
    temperature: float = 0.7
    max_tokens: int = 1024


class RAGChain:
    """端到端 RAG 问答链"""

    # 预设生成方案
    PRESETS = {
        "precise": RAGConfig(top_k=3, temperature=0.1, max_tokens=512),
        "balanced": RAGConfig(top_k=5, temperature=0.5, max_tokens=1024),
        "creative": RAGConfig(top_k=8, temperature=0.9, max_tokens=2048),
    }

    # 默认提示模板
    DEFAULT_SYSTEM_PROMPT = (
        "你是一个基于知识库的智能问答助手。"
        "请根据提供的背景信息回答用户问题。"
        "如果背景信息不足以回答，请如实告知，不要编造内容。"
    )
    DEFAULT_PROMPT_TEMPLATE = (
        "背景信息：\n{context}\n\n"
        "对话历史：\n{history}\n\n"
        "用户问题：{query}\n"
        "回答："
    )

    def __init__(
        self,
        tenant_id: str,
        kb_id: str,
        *,
        llm: Optional[BaseLLM] = None,
        model_name: Optional[str] = None,
        retriever: Optional[HybridRetriever] = None,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        prompt_template: str = DEFAULT_PROMPT_TEMPLATE,
        default_config: Optional[Union[RAGConfig, Dict]] = None,
    ):
        self.tenant_id = tenant_id
        self.kb_id = kb_id
        self.llm = llm or get_llm(model_name)
        self.retriever = retriever or HybridRetriever(use_rerank=True)
        self.system_prompt = system_prompt
        self.prompt_template = prompt_template

        # 实例级默认生成参数
        if default_config is None:
            self.default_config = RAGConfig()
        elif isinstance(default_config, dict):
            self.default_config = RAGConfig(**default_config)
        else:
            self.default_config = default_config

    @staticmethod
    def _format_history(history: Optional[List[Dict[str, str]]]) -> str:
        if not history:
            return "（无历史对话）"
        lines = []
        for turn in history[-6:]:
            role = "用户" if turn["role"] == "user" else "助手"
            lines.append(f"{role}：{turn['content']}")
        return "\n".join(lines)

    async def astream(
        self,
        query: str,
        *,
        top_k: Optional[int] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        history: Optional[List[Dict[str, str]]] = None,
        preset: Optional[str] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """
        异步流式问答

        参数优先级：显式传入 > 预设方案 > 实例默认值
        """
        config = self._resolve_config(top_k, temperature, max_tokens, preset)

        # 1. 混合检索
        try:
            docs = await self.retriever.retrieve(
                query=query,
                tenant_id=self.tenant_id,
                kb_id=self.kb_id,
                top_k=config.top_k,
            )
        except Exception as e:
            logger.error(f"检索异常: {e}")
            yield "[ERROR] 知识库检索失败，请稍后重试。"
            return

        if not docs:
            yield "抱歉，知识库中未找到相关信息。"
            return

        # 2. 组装 Prompt
        context = "\n---\n".join([doc.page_content for doc in docs])
        history_text = self._format_history(history)
        prompt = self.prompt_template.format(
            context=context,
            history=history_text,
            query=query,
        )

        # 3. 流式生成
        try:
            async for chunk in self.llm.agenerate(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                **kwargs,
            ):
                yield chunk
        except Exception as e:
            logger.error(f"LLM 生成失败: {e}")
            yield "[ERROR] 生成回答时出现故障，请稍后重试。"

    async def generate(self, query: str, **kwargs) -> str:
        """非流式生成（聚合流式结果）"""
        parts = []
        async for chunk in self.astream(query, **kwargs):
            parts.append(chunk)
        return "".join(parts)

    def _resolve_config(
        self,
        top_k: Optional[int],
        temperature: Optional[float],
        max_tokens: Optional[int],
        preset: Optional[str],
    ) -> RAGConfig:
        """融合预设、默认值与显式参数"""
        if preset and preset in self.PRESETS:
            base = self.PRESETS[preset]
            logger.debug(f"应用预设方案: {preset}")
        else:
            base = self.default_config

        return RAGConfig(
            top_k=top_k if top_k is not None else base.top_k,
            temperature=temperature if temperature is not None else base.temperature,
            max_tokens=max_tokens if max_tokens is not None else base.max_tokens,
        )


def get_rag_chain(
    tenant_id: str,
    kb_id: str,
    model_name: Optional[str] = None,
    **kwargs,
) -> RAGChain:
    """快速获取 RAG 问答链实例"""
    return RAGChain(tenant_id=tenant_id, kb_id=kb_id, model_name=model_name, **kwargs)