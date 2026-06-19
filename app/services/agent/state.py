# app/services/agent/state.py
"""
Agent 共享状态 —— 支持结构化历史、引用与侧边栏摘要

关键新增：
- SessionItem：一对一问答回合的结构，便于引用特定回答
- conversation_history：所有历史回合的列表（累加）
- input_summary：当前提问的前20字，用于侧边栏显示
"""

from typing import TypedDict, Optional, List, Dict, Any


class SessionItem(TypedDict, total=False):
    """
        一轮完整的对话回合（用户提问 + 智能体回答）

    session_id: str               # 唯一标识，如 "turn_1", "turn_2"
    user_query: str               # 用户原始提问
    query_summary: str            # 用户提问的前20字（用于侧边栏列表）
    agent_response: str           # 智能体最终回答
    timestamp: float              # 创建时间戳

        """
    session_id: str
    user_query: str
    query_summary: str
    agent_response: str
    timestamp: float

    referenced_docs: List[str]
    used_tools: List[str]


class AgentState(TypedDict, total=False):
    """
       多智能体工作流状态
       """

    tenant_id: str
    kb_id: Optional[str]

    #全链路追踪 ID
    trace_id: Optional[str]

    # 轮次数据
    query: str
    input_summary: str

    # 历史，记忆
    chat_history: List[Dict[str, str]]
    conversation_history: List[SessionItem] # 短期记忆载体

    # 中期记忆（对超出窗口历史的压缩摘要）
    memory_summary: Optional[str]

    # 长期记忆（从持久化存储中检索的相关历史）
    long_term_memories: Optional[List[Dict[str, Any]]]

    # 中间产物 retrieved_docs: 检索节点
    # emotion: 情感分析节点
    # tool_result: 如果 Supervisor 决定调用工具，工具执行的结果会暂存这里。
    retrieved_docs: List[Dict[str, Any]]
    emotion: Optional[Dict[str, Any]]
    tool_calls: List[Dict[str, Any]]
    tool_result: Optional[str]

    # ---------- 最终输出 ----------
    final_answer: Optional[str]

    # ---------- 路由与控制 ----------
    # next_node: 状态机的方向盘

    next_node: str
    error: Optional[str]
