# app/services/embedding/m3e.py
"""
M3E 嵌入模型实现，基于 sentence-transformers 库。
默认使用 moka-ai/m3e-base 模型，可通过构造函数更换其他 SentenceTransformer 兼容模型。
所有嵌入向量均做 L2 归一化处理，与 Chroma 余弦度量匹配。
"""
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import numpy as np

from app.services.embedding.base import BaseEmbedding
from app.utils.logger import logger


class M3EEmbedding(BaseEmbedding):
    def __init__(
        self,
        model_name: str = "moka-ai/m3e-base",
        device: Optional[str] = None,
    ):
        """
        初始化 M3E 嵌入模型
        :param model_name: SentenceTransformer 模型名称或本地路径
        :param device: 设备（'cpu', 'cuda'等），为 None 时自动选择
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name, device=device)
        logger.info(f"Embedding model loaded: {model_name}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量文本向量化，返回归一化后的向量列表"""
        if not texts:
            return []
        embeddings = self.model.encode(
            list(texts),
            normalize_embeddings=True,      # L2 归一化
            show_progress_bar=False,
            batch_size=32,
        )
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """单条查询向量化，返回归一化向量"""
        if not text:
            return []
        embedding = self.model.encode(
            [text],
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embedding[0].tolist()