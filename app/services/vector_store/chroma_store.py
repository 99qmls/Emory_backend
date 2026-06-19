# app/services/vector_store/chroma_store.py
import chromadb
from chromadb.config import Settings
from app.services.vector_store.base import BaseVectorStore
from app.core.config import settings as app_settings
from app.utils.logger import logger


class ChromaVectorStore(BaseVectorStore):
    """
    Chroma 向量存储实现（支持多租户隔离）

    租户通过独立的 PersistentClient 路径实现隔离，
    每个知识库对应一个 Collection，命名规则： tenant_{tenant_id}_kb_{kb_id}
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        persist_dir = f"{app_settings.CHROMA_PERSIST_DIR}/tenant_{tenant_id}"
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        logger.debug(f"Chroma client created for tenant {tenant_id} at {persist_dir}")

    def get_collection(self, kb_id: str):
        """
        获取或创建知识库对应的 Chroma Collection。
        返回原生的 chromadb Collection 对象（兼容 LangChain 封装）。
        """
        collection_name = f"tenant_{self.tenant_id}_kb_{kb_id}"
        return self.client.get_or_create_collection(collection_name)

    # 以下为便捷方法，直接在向量存储层面进行增删查

    def add_documents(
        self,
        kb_id: str,
        documents: list,
        embeddings: list,
        metadatas: list = None,
        ids: list = None,
    ):
        collection = self.get_collection(kb_id)
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def query(
        self,
        kb_id: str,
        query_embeddings: list,
        n_results: int = 5,
    ):
        collection = self.get_collection(kb_id)
        return collection.query(query_embeddings=query_embeddings, n_results=n_results)