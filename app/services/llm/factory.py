# app/services/llm/factory.py
"""
LLM 工厂函数 —— 根据模型标识动态返回 BaseLLM 实例，并校验本地模型可用性

支持的标识格式：
  - "ollama:deepseek-r1:7b"   → 本地 Ollama 模型（自动检查是否存在）
  - "openai:gpt-4o"           → 云端兼容 OpenAI 协议的模型（DeepSeek, 智谱等）
若未传入模型名，使用 settings.DEFAULT_LLM_MODEL
"""

from app.services.llm.base import BaseLLM
from app.core.config import settings
from app.utils.logger import logger


def get_llm(model_name: str = None) -> BaseLLM:
    """
    获取 LLM 实例

    参数:
        model_name: 模型标识字符串，例如 "ollama:deepseek-r1:7b" 或 "openai:deepseek-chat"

    返回:
        BaseLLM 子类实例

    异常:
        ValueError: 当指定的本地模型不存在时抛出，提示用户重新输入
    """
    original_name = model_name
    name = model_name or settings.DEFAULT_LLM_MODEL

    if not name or name.strip() == "":
        raise ValueError("未配置任何模型，请在 .env 中设置 DEFAULT_LLM_MODEL 或传入 model_name")

    # 本地 Ollama 模型
    if name.startswith("ollama:"):
        model_id = name.split(":", 1)[1]
        # 启动前验证本地模型是否存在
        _check_local_model_available(model_id)
        from app.services.llm.ollama import OllamaLLM
        logger.info(f"选择本地模型: {model_id}")
        return OllamaLLM(model=model_id)

    # 云端 OpenAI 兼容模型（DeepSeek, 智谱, OpenAI 等）
    if name.startswith("openai:"):
        model_id = name.split(":", 1)[1]
        from app.services.llm.openai import OpenAILLM
        logger.info(f"选择云端模型: {model_id}")
        return OpenAILLM(model=model_id)

    # 兜底：如果没有前缀，尝试作为 OpenAI 模型直接使用（向后兼容）
    logger.warning(f"模型标识 '{name}' 缺少前缀，将默认使用 OpenAI 协议")
    from app.services.llm.openai import OpenAILLM
    return OpenAILLM(model=name)


def _check_local_model_available(model_id: str) -> None:
    """检查本地 Ollama 模型是否已下载，不存在时抛出 ValueError"""
    try:
        import ollama
        # 调用 show 获取模型信息，如果模型不存在会抛出异常
        ollama.show(model_id)
        logger.debug(f"本地模型 {model_id} 已就绪")
    except Exception as e:
        available = _list_local_models()
        hint = f"可用模型: {', '.join(available)}" if available else "未发现任何已下载的模型"
        raise ValueError(
            f"本地模型 '{model_id}' 不存在。{hint}。请运行 `ollama pull {model_id}` 下载，或检查输入是否正确。"
        ) from e


def _list_local_models() -> list:
    """获取已下载的本地模型名称列表"""
    try:
        import ollama
        models = ollama.list()
        # 返回模型名列表
        return [m['name'] for m in models.get('models', [])]
    except Exception:
        return []