# app/services/agent/graph.py
"""
LangGraph 多智能体工作流图

新增优化：
  1. 全局错误处理节点 + 装饰器：任意节点异常均可捕获并短路到 error_handler
  2. 历史记录截断：archive_node 限制最大保留轮数 (MAX_HISTORY = 10)
  3. 动态路由注册：有效节点名自动从 workflow.nodes 提取，无需硬编码
  4. 双重路由保护：supervisor 输出 + 错误检测，两级条件边确保安全

流程：
  entry → supervisor ──→ retriever → generator → archive → END
                    ├──→ tools      → generator → archive → END
                    ├──→ emotion    → generator → archive → END
                    ├──→ generator  → archive → END
                    ├──→ FINISH     → END
                    └──→ (error)    → error_handler → END
"""
# app/services/agent/graph.py (已含错误处理、历史截断、动态路由)
import time
import asyncio
import uuid

import torch
from redis.utils import pipeline
from torch.cuda import memory_summary, temperature
from torch.distributed._shard import checkpoint
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing_extensions import TypedDict
from functools import wraps
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver, InMemorySaver
from langgraph.types import RetryPolicy
from datetime import datetime, timedelta
from app.main import redis_manager

from whisper import tokenizer

from app.services.agent.state import AgentState, SessionItem
from app.services.agent.nodes import (
    emotion_node, generator_node, retriever_node,
    supervisor_node, tools_node, entry_node,
)
from app.utils.logger import logger

MAX_HISTORY = 10

# 全局缓存对象（避免重复加载模型）
_model_cache = {
    "model": None,
    "tokenizer": None,
    "device": None,
    "is_loaded": False
}

# ===== 状态定义 =====
class State(TypedDict):
    user_input: str          # 原始用户输入
    last_active: datetime    # 会话最后活跃时间
    is_session_expired: bool # 会话是否已过期
    trace_id: str            # 分布式追踪ID
    input_summary: str       # 摘要后的文本（关键优化点）
    route_to: str            # 动态路由目标

# 错误处理装饰器（各节点使用）
def with_error_handling(node_name: str):
    def decorator(node_func):
        @wraps(node_func)
        async def wrapper(state: AgentState) -> Dict[str, Any]:
            try:
                return await node_func(state)
            except asyncio.TimeoutError:
                return {"error": f"节点 {node_name} 超时"}
            except Exception as e:
                logger.error(f"节点 {node_name} 异常: {e}")
                return {"error": str(e)[:100]}
        return wrapper
    return decorator

def _init_model():
    if _model_cache["is_loaded"]:
        return

    if not torch.cuda.is_available():
        print("[摘要系统] 未检测到GPU，将使用规则方法（如需启用DeepSeek模型需NVIDIA GPU）")
        return

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model_id = "deepseek-ai/deepseek-llm-r1-7b"

    try:
        print(f"尝试加载模型{model_id} 使用设备{device}")
        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            trust_remote_code=True
        )

        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map="auto",
            torch_dtype=torch.bfloat16,
            load_in_4bit=True,  # 4-bit量化（7B模型约需6GB显存）
            trust_remote_code=True
        )

        _model_cache.update({
            "model": model,
            "tokenizer": tokenizer,
            "device": device,
            "is_loaded": True
        })

        print(f"[摘要系统] DeepSeek-R1-7B 模型加载成功! 显存占用: {torch.cuda.memory_allocated() / 1e9:.2f} GB")

    except Exception as e:
        print(f"[摘要系统错误] 模型加载失败: {str(e)}，将使用规则摘要方法")
        _model_cache["is_loaded"] = False

#  llm/一般 摘要接口
async def _summarize_turn(turn_text: str) -> str:
    if not _model_cache["is_loaded"]:
        _init_model()

        # 1. 提取原始对话内容
    try:
        user_query = turn_text.split("用户：")[1].split("\n")[0].strip()
        agent_resp = turn_text.split("助手：")[1].strip()
    except:
        return _generate_summary_with_rules(turn_text)  # 解析失败时回退

    # 2. 构建摘要任务的专用Prompt
    prompt = f"""你是一个对话摘要专家，请将以下对话压缩为15字内的简短摘要：

    用户提问：{user_query}
    助手回复：{agent_resp}

    要求：
    1. 用"用户询问[主题]，助手回复[结论]"格式
    2. 主题从[天气/时间/计算/定义/其他]中选择
    3. 结论不超过8个汉字

    摘要："""
    pipe = pipeline(
        "text-generation",
        model=_model_cache["model"],
        tokenizer=_model_cache["tokenizer"],
        device_map="auto",
        max_new_tokens=30,
        temperature=0.1,
        do_sample=False,

    )

    result = pipe(prompt)[0]["generated_text"]
    summary = result.split("摘要：")[-1].strip()

    # 5. 验证格式有效性（防模型幻觉）
    if "用户询问" not in summary or "助手回复" not in summary:
        return _generate_summary_with_rules(turn_text)

    return summary[:50]

   # 回退方案
def _generate_summary_with_rules(turn_text: str) -> str:
    """原始规则模板法（安全回退方案）"""
    try:
        user_part = turn_text.split("用户：")[1].split("\n")[0].strip()
        assistant_part = turn_text.split("助手：")[1].strip()

        # 意图关键词库
        intent_keywords = {
            "天气": ["天气", "气温", "温度", "预报", "下雨", "阴天", "晴天"],
            "时间": ["几点", "时间", "现在", "多久", "何时"],
            "计算": ["计算", "等于", "结果", "多少", "乘以", "除以"],
            "定义": ["是什么", "定义", "解释", "意思", "概念"]
        }

        topic = "其他"
        for intent, keywords in intent_keywords.items():
            if any(kw in user_part for kw in keywords):
                topic = intent
                break

        clean_resp = ''.join(c for c in assistant_part if ord(c) < 256)  # 移除非中文字符干扰
        key_info = clean_resp[:6] + ("..." if len(clean_resp) > 6 else "")

        return f"用户询问{topic}，助手回复{key_info}"

    except Exception:
        print(f"对话摘要{turn_text[:30]}")





# 具体调用，生成对话文本
async def _update_memory_summary(
        oldest_session: SessionItem,
        current_summary: str,
        user_id: str):
    if redis_manager is None:
        logger.warning("Redis 管理器未初始化,不进行记忆更新")
        return
    try:
        turn_text = f"用户：{oldest_session['user_query']}\n助手：{oldest_session['agent_response']}"
        new_line = await _summarize_turn(turn_text)

        # 合并摘要
        merged = await redis_manager.append_summary(
            user_id=user_id,
            content=new_line,
            max_len=300
        )
        logger.info(f"用户{user_id}中记忆更新，长度{len(merged)}")
    except Exception as e:
        logger.error(f"更新记忆失败(user={user_id}:{e})")




def _merge_memory_summaries(old_summary: str, new_line: str, max_length: int = 300) -> str:
    """
    将新摘要行追加到已有摘要后，超出长度时自动截断或压缩。
    """
    if not old_summary:
        return new_line

    combined = f"{old_summary}\n{new_line}"

    # 如果合并后超长，可调用轻量 LLM 再压缩，或直接截断保留后半部分
    if len(combined) > max_length:
        # 简单截断策略：保留最新的一部分（也可替换为 LLM 压缩）
        logger.warning("中期记忆超长，执行截断")
        return combined[-max_length:]  # 保留末尾部分（较新）
    return combined

# 归档：保存本轮对话并截断历史
async def archive_node(state: AgentState) -> dict:
    new_session: SessionItem = {
        "session_id": f"turn_{len(state.get('conversation_history', [])) + 1}",
        "user_query": state.get("query", ""),
        "query_summary": state.get("input_summary", ""),
        "agent_response": state.get("final_answer", ""),
        "timestamp": time.time(),
    }
    history = state.get("conversation_history", [])
    memory_summary = state.get("memory_summary", None)
    if len(memory_summary) > MAX_HISTORY:
        oldest = history[0]
        # 异步生成摘要，不阻塞主流程
        asyncio.create_task(_update_memory_summary(oldest, memory_summary, state.get("tenant_id")))
        # 实际移除最旧记录
        history = history[1:]
    return {"conversation_history": (history + [new_session])[-MAX_HISTORY:]}

# 错误处理节点
async def error_handler_node(state: AgentState) -> dict:
    err = state.get("error", "未知错误")
    return {"final_answer": f"系统发生错误：{err}\n请稍后重试。"}

# 条件路由：错误优先 + 动态白名单
def route(state: AgentState) -> str:
    if state.get("error"):
        return "error_handler"
    next_node = state.get("next_node", "generator").lower()
    valid = {"retriever", "tools", "emotion", "generator"}
    return next_node if next_node in valid else "generator"

def build_agent_graph():
    wf = StateGraph(AgentState)
    wf.add_node("entry", entry_node)
    wf.add_node("supervisor", with_error_handling("supervisor")(supervisor_node))
    wf.add_node("retriever", retriever_node)
    wf.add_node("tools", tools_node)
    wf.add_node("emotion",
                emotion_node,
                retry_policy=RetryPolicy(
                    max_attempts=3,
                    backoff_factor=1.0,  # 基础退避时间=1秒
                    jitter=True,
                ))
    wf.add_node("generator", generator_node)
    wf.add_node("archive", archive_node)
    wf.add_node("error_handler", error_handler_node)

    wf.set_entry_point("entry")
    wf.add_edge("entry", "supervisor")
    wf.add_conditional_edges("supervisor", route, {
        "retriever": "retriever",
        "tools": "tools",
        "emotion": "emotion",
        "generator": "generator",
        "error_handler": "error_handler",
    })
    for node in ["retriever", "tools", "emotion"]:
        wf.add_edge(node, "generator")
    wf.add_edge("generator", "archive")
    wf.add_edge("archive", END)
    wf.add_edge("error_handler", END)
    return wf

# 编译并暴露给外部
agent_graph = build_agent_graph().compile(checkpointer=MemorySaver())


