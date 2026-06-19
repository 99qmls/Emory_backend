# app/utils/sse.py
"""
Server-Sent Events 流式响应辅助工具
"""
import json
from typing import Any, Optional


def sse_format(data: Any, event: Optional[str] = None, retry: Optional[int] = None) -> str:
    """
    生成一条 SSE 规范格式的消息字符串
    :param data: 要发送的数据（会自动转为 JSON）
    :param event: 可选的事件名
    :param retry: 客户端重连间隔（毫秒）
    :return: 格式化后的 SSE 字符串
    """
    msg_parts = []
    if event:
        msg_parts.append(f"event: {event}")
    if retry is not None:
        msg_parts.append(f"retry: {retry}")
    # data 必须放在最后，且多行需正确处理（这里简单序列化为一行 JSON）
    msg_parts.append(f"data: {json.dumps(data, ensure_ascii=False)}")
    return "\n".join(msg_parts) + "\n\n"


def sse_done() -> str:
    """发送结束标记，客户端可据此关闭连接"""
    return "data: [DONE]\n\n"


def sse_error(message: str) -> str:
    """发送错误事件"""
    return sse_format({"error": message}, event="error")