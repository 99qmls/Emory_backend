# app/services/agent/nodes/retriever.py
"""
检索节点 —— 生产级增强检索，支持租户隔离、安全截断与三级降级
解决评审中提出的租户隔离、语义截断和故障恢复问题
"""
import asyncio
import re
from typing import Dict, Any, List, Optional, Callable

from app.services.agent.state import AgentState
from app.services.rag.retriever import HybridRetriever
from app.core.retriever import TenantIsolatedRetriever
from app.utils.logger import logger

# --------------------------
# 租户安全隔离的检索器工厂
# --------------------------
_instances: Dict[str, HybridRetriever] = {}
_lock = asyncio.Lock()


@classmethod
async def get_retriever(cls, tenant_id: str) -> HybridRetriever:
    if tenant_id not in cls._instances:
        async with cls._lock:
            if tenant_id not in cls._instances:
                cls._instances[tenant_id] = HybridRetriever(
                    use_rerank=True,
                )
                logger.info(f"租户创建独立检索器:{tenant_id}")
    return cls._instances[tenant_id]


# --------------------------
# 安全截断工具
# --------------------------
def safe_truncate(text: str, max_len: int) -> str:
    """
       安全截断：优先在句号、换行等自然边界处截断，避免破坏词语完整性。
       若没有合适边界，至少保证不以非法字符结束。
       """
    if len(text) <= max_len:
        return text
    truncated = text[:max_len]
    match = re.search(r'[。！？\n]', truncated[::-1])
    if match:
        last_break = max_len - match.start()
        return text[:last_break].rstrip()
    return truncated.rstrip()


MAX_QUERY_LENGTH = 200  # 最终发送给检索器的最大字符数


def _build_enriched_query(
        query: str,
        conversation_history: List[dict],
        referred_session_ids: Optional[List[str]] = None,
) -> str:
    clean_query = query.strip() or "无有效内容"

    if referred_session_ids:
        session_map = {s.get("session_id"): s for s in conversation_history if s.get("session_id")}
        valid_contents = []
        for sid in referred_session_ids:
            session = session_map.get(sid)
            if not session:
                continue
            agent_response = session.get("agent_response", "").strip()
            if agent_response and len(agent_response) > 20:
                valid_contents.append(agent_response)

        if valid_contents:
            sorted_contents = sorted(valid_contents, key=len, reverse=True)[:2]
            context = " | ".join(cont[:300] for cont in sorted_contents)
            return f"关键参考：{context}\n当前问题：{clean_query}"

    if len(conversation_history) >= 2:
        prev_query = conversation_history[-2].get("user_query", "").strip()
        if prev_query and prev_query != clean_query and len(prev_query) > 10:
            return f"背景：{prev_query[:100]}\n问题：{clean_query}"

    return clean_query

# --------------------------
# 节点主函数（三级降级）
# --------------------------
async def retriever_node(state: AgentState) -> Dict[str, Any]:
    """
    执行带租户隔离、历史增强的安全检索。
    返回状态中包含结构化状态码，便于上层决策。
    """
    query = state.get("query", "").strip()
    tenant_id = state.get("tenant_id", "")
    kb_id = state.get("kb_id")

    if not query or not tenant_id:
        return {"retrieved_docs": [], "retrieval_status": "skipped"}

    if not kb_id:
        return {"retrieved_docs": [], "retrieval_status": "no_kb"}

    # 1. 获取租户专属检索器
    try:
        retriever = await TenantIsolatedRetriever.get_retriever(tenant_id)
    except Exception as e:
        logger.critical(f"租户检索器初始化失败: {e}")
        return {"retrieved_docs": [], "retrieval_status": "failed"}

    # 2. 构建增强查询并安全截断
    enhanced = _build_enriched_query(
        query=query,
        conversation_history=state.get("conversation_history", []),
        referred_session_ids=state.get("referred_session_ids"),
    )
    final_query = safe_truncate(enhanced, MAX_QUERY_LENGTH)
    if len(final_query) < len(enhanced):
        logger.info(f"查询被安全截断: {len(enhanced)} -> {len(final_query)} 字符")

    # 3. 三级降级检索
    try:
        # 第一级：增强查询完整检索
        docs = await retriever.retrieve(
            query=final_query,
            tenant_id=tenant_id,
            kb_id=kb_id,
            top_k=5,
        )
        if docs:
            return _format_success(docs)
        else:
            # 第二级：无结果，尝试基础查询（无增强）
            logger.info("增强查询无结果，尝试基础查询")
            base_query = safe_truncate(query, MAX_QUERY_LENGTH)
            docs = await retriever.retrieve(
                query=base_query,
                tenant_id=tenant_id,
                kb_id=kb_id,
                top_k=3,
            )
            if docs:
                return _format_success(docs, status="degraded_no_results")
            else:
                return {"retrieved_docs": [], "retrieval_status": "no_results"}

    except asyncio.TimeoutError:
        logger.warning(f"检索超时 {tenant_id}，降级基础查询")
        try:
            docs = await retriever.retrieve(
                query=query[:MAX_QUERY_LENGTH],  # 原始查询截断
                tenant_id=tenant_id,
                kb_id=kb_id,
                top_k=3,
            )
            if docs:
                return _format_success(docs, status="degraded_timeout")
            else:
                return {"retrieved_docs": [], "retrieval_status": "degraded_timeout_no_results"}
        except Exception:
            return {"retrieved_docs": [], "retrieval_status": "failed_timeout"}

    except Exception as e:
        logger.error(f"检索致命错误 {tenant_id}: {type(e).__name__}", exc_info=True)
        return {"retrieved_docs": [], "retrieval_status": "failed", "error": str(e)[:100]}


def _format_success(docs: List, status: str = "success") -> Dict[str, Any]:
    """将检索文档格式化为状态字典"""
    retrieved = [
        {
            "page_content": doc.page_content,
            "metadata": doc.metadata,
            "score": doc.metadata.get("retrieval_score", 0.0)
        }
        for doc in docs
    ]
    return {"retrieved_docs": retrieved, "retrieval_status": status}



