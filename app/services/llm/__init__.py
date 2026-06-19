# app/services/llm/__init__.py
"""
LLM 推理层导出模块

提供的公开接口：
- get_llm：工厂函数，根据配置或运行时参数获取 LLM 实例
- BaseLLM：抽象基类，所有 LLM 适配器必须实现
"""

from app.services.llm.factory import get_llm
from app.services.llm.base import BaseLLM

__all__ = ["get_llm", "BaseLLM"]