# app/services/embedding/factory.py
"""
嵌入模型工厂，根据配置返回合适的 Embedding 实例。
支持的模型名称：'m3e' 或任何 SentenceTransformer 兼容名称。
"""
from app.services.embedding.base import BaseEmbedding
from app.services.embedding.m3e import M3EEmbedding
from app.utils.logger import logger


def get_embedding_model(model_name: str = "m3e") -> BaseEmbedding:
    """
    获取嵌入模型实例
    :param model_name: 模型标识，例如 'm3e' 会加载默认的 moka-ai/m3e-base
    :return: BaseEmbedding 实例
    """
    if model_name == "m3e":
        return M3EEmbedding()
    # 多版本扩展点：可在此处增加其他嵌入模型（如 text2vec-large-chinese 等）
    logger.warning(f"未知的嵌入模型标识 '{model_name}'，将尝试作为 SentenceTransformer 名称加载")
    return M3EEmbedding(model_name=model_name)