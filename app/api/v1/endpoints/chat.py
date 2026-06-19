import json
from typing import Any, AsyncGenerator
from uuid import UUID
import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.config import settings
from app.core.database import get_db
from app.crud.crud_conversation import conversation_crud, message_crud
from app.models.user import User
from app.schemas.chat import ChatRequest, MessageResponse
from app.services.rag.chain import get_rag_chain
from app.services.agent.graph import agent_graph

router = APIRouter()


@router.post("/stream")
async def chat(
        *,
        db: AsyncSession = Depends(get_db),
        chat_req: ChatRequest,
        current_user: User = Depends(deps.get_current_user),
) -> StreamingResponse:
    # 1. 会话处理
    conversation_id = chat_req.conversation_id
    if conversation_id:
        conv = await conversation_crud.get(db, id=conversation_id)
        if not conv or conv.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="会话不存在")
    else:
        from app.schemas.conversation import ConversationCreate
        conv_in = ConversationCreate(
            title=chat_req.query[:50],
            mode="knowledge" if chat_req.kb_id else "mixed",
            kb_id=chat_req.kb_id
        )
        conv = await conversation_crud.create_with_user(db, obj_in=conv_in, user_id=current_user.id)
        conversation_id = conv.id

    # 2. 保存用户消息
    from app.schemas.message import MessageCreate
    user_msg_in = MessageCreate(
        conversation_id=conversation_id,
        role="user",
        content=chat_req.query
    )
    await message_crud.create(db, obj_in=user_msg_in)

    # 3. 流式生成器
    async def event_generator() -> AsyncGenerator[str, None]:
        full_response = ""
        yield f"data: {json.dumps({'conversation_id': str(conversation_id)}, ensure_ascii=False)}\n\n"
        try:
            if chat_req.kb_id:
                # ---------- RAG 分支 ----------
                chain = get_rag_chain(
                    tenant_id=str(current_user.tenant_id),
                    kb_id=str(chat_req.kb_id)
                )
                async for content in chain.astream(chat_req.query):
                    if content:
                        full_response += content
                        yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
            else:
                # ---------- Multi-Agent 分支 ----------
                # 构建 config（检查点必需）
                if chat_req.config and "configurable" in chat_req.config:
                    agent_config = chat_req.config
                else:
                    agent_config = {"configurable": {"thread_id": str(conversation_id)}}

                inputs = {
                    "query": chat_req.query,
                    "tenant_id": str(current_user.tenant_id),
                    "kb_id": str(chat_req.kb_id) if chat_req.kb_id else None,
                    "chat_history": [],
                    "conversation_id": str(conversation_id)
                }

                print(f"[DEBUG] 准备调用 agent_graph.astream，inputs={inputs}, config={agent_config}")
                event_count = 0
                async for event in agent_graph.astream(inputs, config=agent_config):
                    event_count += 1
                    print(f"[DEBUG] 收到事件 {event_count}: {event}")
                    # 调试用，发送原始事件给前端（上线前请删除或注释）
                    # yield f"data: {json.dumps({'debug': event}, ensure_ascii=False)}\n\n"

                    if "generator" in event:
                        final_answer = event["generator"].get("final_answer", "")
                        if final_answer:
                            full_response += final_answer
                            yield f"data: {json.dumps({'content': final_answer}, ensure_ascii=False)}\n\n"

                if event_count == 0:
                    print("[WARNING] agent_graph.astream 未产生任何事件！")
                    yield f"data: {json.dumps({'warning': 'No events from agent_graph'}, ensure_ascii=False)}\n\n"

        except Exception as e:
            print(f"[ERROR] 流式异常: {e}")
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
        finally:
            # 4. 保存助手消息
            content_to_save = full_response.strip() or "（空响应）"
            model_name = chat_req.model or settings.DEFAULT_LLM_MODEL
            token_count = len(full_response.split())

            from app.models.message import Message
            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=content_to_save,
                model_name=model_name,
                token_count=token_count,
                created_at=datetime.datetime.utcnow(),
                updated_at=datetime.datetime.utcnow(),
            )
            db.add(assistant_msg)
            await db.commit()
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


@router.get("/conversations/{conv_id}/messages", response_model=list[MessageResponse])
async def get_messages(
        conv_id: UUID,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(deps.get_current_user),
) -> Any:
    conv = await conversation_crud.get_with_messages(db, conv_id=conv_id, user_id=current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    return conv.messages


@router.delete("/conversations/{conv_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
        conv_id: UUID,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(deps.get_current_user),
) -> None:
    conv = await conversation_crud.get(db, id=conv_id)
    if not conv or conv.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="会话不存在")
    await conversation_crud.delete(db, id=conv_id)
