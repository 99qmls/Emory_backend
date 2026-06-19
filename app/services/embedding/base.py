# app/services/embedding/base.py
from abc import ABC, abstractmethod
from typing import List


class BaseEmbedding(ABC):
    """嵌入模型抽象基类，定义所有嵌入服务必须实现的接口"""

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        将一批文档转换为向量列表（每个向量是一个浮点数列表）
        :param texts: 文本列表
        :return: 与 texts 等长的向量列表
        """
        pass

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """
        将单个查询文本转换为向量
        :param text: 查询文本
        :return: 向量
        """
        pass