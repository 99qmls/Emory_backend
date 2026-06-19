# app/services/vector_store/base.py
from abc import ABC, abstractmethod


class BaseVectorStore(ABC):
    """向量数据库统一接口"""

    @abstractmethod
    def get_collection(self, kb_id: str):
        """根据知识库ID获取对应的集合对象（具体类型由子类决定）"""
        pass