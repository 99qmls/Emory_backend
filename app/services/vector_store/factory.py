# app/services/vector_store/factory.py
from app.services.vector_store.chroma_store import ChromaVectorStore


def get_vector_store(tenant_id: str) -> ChromaVectorStore:
    """
    获取指定租户的向量存储实例。
    目前仅支持 Chroma 作为后端。
    """
    return ChromaVectorStore(tenant_id)