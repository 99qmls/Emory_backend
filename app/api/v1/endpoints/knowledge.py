# app/api/v1/endpoints/knowledge.py
from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.core.database import get_db
from app.core.config import settings
from app.crud.crud_knowledge import knowledge_crud
from app.crud.crud_document import document_crud
from app.schemas.knowledge import KnowledgeBaseCreate, KnowledgeBaseUpdate, KnowledgeBaseResponse
from app.schemas.document import DocumentResponse
from app.models.user import User
from app.utils.minio_client import minio_client
from app.services.tasks.document_tasks import process_document

router = APIRouter()


@router.post("/", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
async def create_kb(
    *,
    db: AsyncSession = Depends(get_db),
    kb_in: KnowledgeBaseCreate,
    tenant_id: UUID = Depends(deps.get_current_tenant_id),
    _: User = Depends(deps.get_current_admin_user),
) -> Any:
    """创建知识库（管理员）"""
    kb = await knowledge_crud.create_with_tenant(db, obj_in=kb_in, tenant_id=tenant_id)
    return kb


@router.get("/", response_model=List[KnowledgeBaseResponse])
async def list_kbs(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    tenant_id: UUID = Depends(deps.get_current_tenant_id),
) -> Any:
    """列出当前租户的知识库"""
    return await knowledge_crud.get_multi_by_tenant(db, tenant_id=tenant_id, skip=skip, limit=limit)


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_kb(
    kb_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(deps.get_current_tenant_id),
) -> Any:
    """获取知识库详情（含文档列表）"""
    kb = await knowledge_crud.get_with_documents(db, kb_id=kb_id, tenant_id=tenant_id)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return kb


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_kb(
    *,
    db: AsyncSession = Depends(get_db),
    kb_id: UUID,
    kb_in: KnowledgeBaseUpdate,
    tenant_id: UUID = Depends(deps.get_current_tenant_id),
    _: User = Depends(deps.get_current_admin_user),
) -> Any:
    """更新知识库（管理员）"""
    kb = await knowledge_crud.get(db, id=kb_id)
    if not kb or kb.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return await knowledge_crud.update(db, db_obj=kb, obj_in=kb_in)


@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kb(
    *,
    db: AsyncSession = Depends(get_db),
    kb_id: UUID,
    tenant_id: UUID = Depends(deps.get_current_tenant_id),
    _: User = Depends(deps.get_current_admin_user),
) -> None:
    """软删除知识库（管理员）"""
    kb = await knowledge_crud.get(db, id=kb_id)
    if not kb or kb.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="知识库不存在")
    await knowledge_crud.delete(db, id=kb_id)


@router.post("/{kb_id}/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    *,
    db: AsyncSession = Depends(get_db),
    kb_id: UUID,
    file: UploadFile = File(...),
    tenant_id: UUID = Depends(deps.get_current_tenant_id),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """上传文档到知识库"""
    # 1. 验证知识库归属
    kb = await knowledge_crud.get(db, id=kb_id)
    if not kb or kb.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="知识库不存在")

    # 2. 限制文件类型（可选）
    allowed_types = ["application/pdf", "text/plain", "text/markdown", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="不支持的文件格式")

    # 3. 保存到 MinIO
    file_path = f"tenant_{tenant_id}/kb_{kb_id}/{file.filename}"
    minio_client.put_object(
        settings.MINIO_BUCKET, file_path, file.file, length=-1, part_size=10*1024*1024
    )

    # 4. 创建文档记录
    from app.schemas.document import DocumentCreate
    doc_in = DocumentCreate(
        kb_id=kb_id,
        file_name=file.filename,
        file_url=file_path,
        file_type=file.content_type,
        status="pending"
    )
    doc = await document_crud.create(db, obj_in=doc_in)

    # 5. 触发异步处理
    process_document.delay(str(doc.id))

    return doc


@router.get("/{kb_id}/documents", response_model=List[DocumentResponse])
async def list_documents(
    kb_id: UUID,
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    tenant_id: UUID = Depends(deps.get_current_tenant_id),
) -> Any:
    """列出知识库下的文档"""
    kb = await knowledge_crud.get(db, id=kb_id)
    if not kb or kb.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return await document_crud.get_multi_by_kb(db, kb_id=kb_id, skip=skip, limit=limit)