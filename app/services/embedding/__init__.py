# app/services/embedding/__init__.py
from .base import BaseEmbedding
from .m3e import M3EEmbedding
from .factory import get_embedding_model

__all__ = ["BaseEmbedding", "M3EEmbedding", "get_embedding_model"]