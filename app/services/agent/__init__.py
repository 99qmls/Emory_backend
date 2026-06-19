# app/services/agent/__init__.py

"""
Agent 服务包的入口。
将 graph 中的编译后对象暴露给外部使用。
"""

from .graph import agent_graph

# 如果有需要，也可以把 State 暴露出来，方便外部类型提示
from .state import AgentState

__all__ = ["agent_graph", "AgentState"]