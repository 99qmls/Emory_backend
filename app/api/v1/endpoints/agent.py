# app/api/v1/endpoints/agent.py
import json
from typing import Any, AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.database import get_db
from app.models.user import User
from app.schemas.chat import ChatRequest
from app.services.agent.graph import agent_graph
from app.crud.crud_conversation import conversation_crud, message_crud

router = APIRouter()


@router.post("/chat")
async def agent_chat(
    *,
    db: AsyncSession = Depends(get_db),
    chat_req: ChatRequest,
    current_user: User = Depends(deps.get_current_user),
) -> StreamingResponse:
    """直接走 LangGraph 多代理链，不受 kb_id 影响"""

    # 获取或创建会话（此处强制创建新会话或复用 ID）
    if chat_req.conversation_id:
        conv = await conversation_crud.get(db, id=chat_req.conversation_id)
        if not conv or conv.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="会话不存在")
        conversation_id = conv.id
    else:
        from app.schemas.chat import ConversationCreate
        conv_in = ConversationCreate(
            title=chat_req.query[:50],
            mode="mixed",
            kb_id=chat_req.kb_id
        )
        conv = await conversation_crud.create_with_user(db, obj_in=conv_in, user_id=current_user.id)
        conversation_id = conv.id

    # 保存用户消息
    from app.schemas.chat import MessageCreate
    user_msg = await message_crud.create(db, obj_in=MessageCreate(
        conversation_id = conversation_id,
        role="user",
        content=chat_req.query
    ))

    async def event_generator() -> AsyncGenerator[str, None]:
        full_response = ""
        try:
            inputs = {
                "query": chat_req.query,
                "tenant_id": str(current_user.tenant_id),
                "kb_id": str(chat_req.kb_id) if chat_req.kb_id else None,
                "chat_history": [],
                "conversation_id": str(conversation_id),
            }
            # LangGraph 流式输出，假设每个节点生成事件包含 content
            async for event in agent_graph.astream(inputs):
                yield f"data: {json.dumps({'debug': event}, ensure_ascii=False)}\n\n"
                # 处理不同类型的节点事件，通常最终生成节点会产出 final_answer
                for node_name, node_output in event.items():
                    if "final_answer" in node_output:
                        content = node_output["final_answer"]
                        full_response += content
                        yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
                # 若需要传递情感标签等中间信息，可额外 emit 自定义事件
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
        finally:
            # 保存助手消息
            assistant_msg = await message_crud.create(db, obj_in=MessageCreate(
                conversation_id=conversation_id,
                role="assistant",
                content=full_response.strip() or "（空响应）",
                model_name=chat_req.model or "agent",
                token_count=len(full_response.split())
            ))
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )