# 高级检索器：混合检索 (向量 + BM25) + 重排序 (BGE-Reranker)
import asyncio
import hashlib
from typing import List, Optional, Dict, Any, Tuple, Set
from collections import defaultdict
import numpy as np
import jieba
# 核心检索包
# from langchain.doctorate.document import Document 该方法废弃
from langchain_core.documents import Document
from langchain_core.callbacks import Callbacks
# 实现层
from langchain_community.vectorstores import Chroma
# bm25实现
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder

from app.services.embedding import m3e
# 自定义业务模块
from app.services.vector_store.factory import get_vector_store
# 支持不同模型切换
from app.services.embedding.factory import get_embedding_model
from app.utils.logger import logger

# 默认模型
DEFAULT_RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"
BM_CACHE_TTL = 300  # 300s


class HybridRetriever:
    """
    混合检索器

    - 向量检索：通过 Chroma 的 collection.query 实现
    - BM25 检索：每次从 Chroma 获取该知识库全部文本构建索引（已做简单缓存优化）
    - 融合：RRF (Reciprocal Rank Fusion)
    - 重排序：BGE‑Reranker 对候选文档重新打分
    """

    # 全局缓存
    _bm25_global_cache: Dict[Tuple[str, str], Tuple[List[Document], BM25Okapi, float]] = {}
    _bm25_locks: Dict[Tuple[str, str], asyncio.Lock] = defaultdict(asyncio.Lock)

    # 初始化逻辑
    def __init__(
            self,
            embedding_model_name: str = "m3e",
            reranker_model_name: str = DEFAULT_RERANKER_MODEL,
            use_rerank: bool = True,
            callbacks: Optional[Callbacks] = None,
    ):
        self.embedding_model = get_embedding_model(embedding_model_name)
        self.reranker = self._load_reranker(reranker_model_name) if use_rerank else None
        self.use_rerank = use_rerank and (self.reranker is not None)
        self.callbacks = callbacks

    def _load_reranker(self, model_name: str) -> Optional[CrossEncoder]:
        """ 安全加载"""
        try:
            return CrossEncoder(model_name, max_length=512, trust_remote_code=True)
        except Exception as e:
            logger.error(f"模型错误:{model_name}is {str(e)},重排序不可用")
            return None

    # BM25 索引缓存机制
    def invalidate_cache(self, tenant_id: str, kb_id: str):
        """当知识库文档变更时清除对应的 BM25 缓存 documents"""
        key = (tenant_id, kb_id)
        if key in self._bm25_global_cache:
            logger.debug(f"Bm25 cache invalidated for tenant={tenant_id},kb={kb_id}")
            del self._bm25_global_cache[key]

    async def _get_all_documents(self, tenant_id: str, kb_id: str) -> List[Document]:
        """从向量库获取知识库的全部文档（协议层标准类型）"""
        store = get_vector_store(tenant_id)

        # 利用 langchain-community 的 Chroma 集成自动转换类型
        vectorstore = Chroma(
            collection_name=kb_id,
            client=store.client,
            embedding_function=self.embedding_model.embedding_documents

        )

        collections = vectorstore._collection

        # 分页获取
        all_docs = []
        offset = 0
        batch_size = 1000

        while True:
            result = collections.get(
                limit=batch_size,
                offset=offset,
                include=["documents", "metadatas", "uris", "data", "embeddings"]
            )
            if not result["ids"]:
                break

            for i in range(len(result["ids"])):
                doc = Document(
                    page_content=result["documents"][i],
                    metadata={
                        **(result["documents"][i] if result["documents"] else {}),
                        "id": result["ids"][i],
                        "source": result["uris"][i] if result["uris"] else None
                    }
                )
                all_docs.append(doc)
            offset += batch_size
        return all_docs

    async def _get_bm25_index(
            self, tenant_id: str, kb_id: str
    ) -> Optional[Tuple[List[Document], BM25Okapi]]:
        """安全获取 BM25 索引（带自动重建和锁机制）"""
        cache_key = (tenant_id, kb_id)

        # 检测首次缓存和验证ttl
        if cache_key in self._bm25_global_cache:
            docs, bm25, timestamp = self._bm25_global_cache[cache_key]
            if asyncio.get_running_loop().time() - timestamp < BM_CACHE_TTL:
                return docs, bm25

        # 加锁并检查
        async with self._bm25_locks[cache_key]:
            if cache_key in self._bm25_global_cache:
                docs, bm25, timestamp = self._bm25_global_cache[cache_key]
                if asyncio.get_running_loop().time() - timestamp < BM_CACHE_TTL:
                    return docs, bm25

            # 构建新索引
            try:
                all_docs = await self._get_all_documents(tenant_id, kb_id)
                if not all_docs:
                    logger.warning(f"知识库无文档: tenant={tenant_id},bk={kb_id}")
                    return None

                tokenized_corpus = [
                    self._chinese_tokenize(doc.page_content)
                    for doc in all_docs
                ]
                bm25 = BM25Okapi(tokenized_corpus)
                # 缓存更新
                self._bm25_global_cache[cache_key] = (
                    all_docs,
                    bm25,
                    asyncio.get_running_loop().time()
                )
                logger.info(f"bm25 索引构建成功: tenant={tenant_id},kb={kb_id}")
                return all_docs, bm25
            except Exception as e:
                logger.error(f"bm25构建失败:[{tenant_id}/{kb_id}]")
                return None

    # 分词
    def _chinese_tokenize(self, text: str) -> List[str]:
        """使用jieba分词"""
        if not text.strip():
            return []
        # 停用词表，可以采用更加完整的
        stopwords = {"的", "了", "和", "是", "就", "都", "而", "及", "与", "或"}
        # 分词过滤
        words = [
            word for word in jieba.lcut(text, cut_all=True)
            if word.strip() and word not in stopwords
        ]
        return words or list(text)

    async def _vector_search(
            self, query: str, tenant_id: str, kb_id: str, top_k: int
    ) -> List[Tuple[Document, float]]:

        store = get_vector_store(tenant_id)
        vectorstore = Chroma(
            collection_name=kb_id,
            client=store.client,
            embedding_function=self.embedding_model.embed_query,
        )
        results = await vectorstore.asimilarity_search_with_score(
            query, k=top_k, callbacks=self.callbacks
        )
        return [(doc, float(score)) for doc, score in results]

    async def _bm25_search(
            self, query: str, tenant_id: str, kb_id: str, top_k: int
    ) -> List[Tuple[Document, float]]:
        """BM25 检索（安全封装）"""
        bm25_result = await self._get_bm25_index(tenant_id, kb_id)
        if not bm25_result:
            return []
        # 分词计算分数
        all_docs, bm25 = bm25_result
        tokenized_query = self._chinese_tokenize(query)
        doc_scores = bm25.get_scores(tokenized_query)

        # 生成结果（带归一化）
        results = []
        for idx, score in enumerate(doc_scores):
            if score <= 0:
                continue
            results.append((all_docs[idx], float(score)))

        # 降序排列
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    # RRF 融合算法实现
    def _rrf_fusion(
            self,
            # vector_results: List[Tuple[Document], float],
            # bm25_results: List[Tuple[Document], float],
            vector_results: List[Tuple[Document, float]],
            bm25_results: List[Tuple[Document, float]],
            k: int = 60,
    ) -> list[tuple[Any, float]]:
        doc_scores = defaultdict(float)
        doc_map = {}  # id -> (Document, 原始分数)

        for rank, (doc, score) in enumerate(vector_results, 1):
            doc_id = doc.id or hashlib.md5(doc.page_content.encode()).hexdigest()
            # RRF 公式
            doc_scores[doc_id] += 1.0 / (k + rank)
            doc_map[doc_id] = (doc, score)

        # 处理 BM25 结果
        for rank, (doc, score) in enumerate(bm25_results, 1):
            doc_id = doc.id or hashlib.md5((doc.page_content.encode())).hexdigest()
            doc_scores[doc_id] += 1.0 / (k + rank)
            if doc_id not in doc_map:
                doc_map[doc_id] = (doc, score)

        sorted_items = sorted(
            doc_scores.items(), key=lambda x: x[1], reverse=True
        )

        return [
            (doc_map[doc_id][0], doc_scores[doc_id])
            for doc_id, _ in sorted_items
        ]

    # 重排序层 (_rerank)
    async def _rerank(
            self, query: str, candidates: List[Tuple[Document, float]]
    ) -> List[Tuple[Document, float]]:
        """重排序（安全降级处理）"""
        if not self.use_rerank or not candidates:
            return [(doc, float(score)) for doc, score in candidates]
        try:
            pairs= [[query,doc.page_content] for doc ,_ in candidates]
            scores= await asyncio.get_running_loop().run_in_executor(
                None, self.reranker.predict, pairs
            )
            return [
                (doc, float(scores[i]))
                for i, (doc, _) in enumerate(candidates)
            ]
        except Exception as e:
            logger.error(f"重排序失败：{str(e)},返回原始结果")
            return [(doc, float(score)) for doc, score in candidates]

