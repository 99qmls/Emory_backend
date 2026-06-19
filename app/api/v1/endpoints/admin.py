# 管理员统计接口 (用户数、Token消耗、QPS等)
# app/api/v1/endpoints/admin.py
from typing import Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.api import deps
from app.core.database import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.models.conversation import Conversation
from app.models.model_usage_log import ModelUsageLog

router = APIRouter()


@router.get("/stats/tenants")
async def get_tenant_stats(
        db: AsyncSession = Depends(get_db),
        _: User = Depends(deps.get_current_superuser),
) -> Any:
    """租户总数、活跃租户数、各计划分布"""
    # 总数
    total = await db.scalar(select(func.count()).select_from(Tenant).where(Tenant))
    active = await db.scalar(
        select(func.count()).select_from(Tenant).where(
            Tenant, Tenant.status == "active"
        )
    )
    # 按计划统计
    plan_stmt = (
        select(Tenant.plan, func.count())
        .where(Tenant)
        .group_by(Tenant.plan)
    )
    plan_rows = (await db.execute(plan_stmt)).all()
    plans = {row[0]: row[1] for row in plan_rows}

    return {
        "total_tenants": total,
        "active_tenants": active,
        "by_plan": plans,
    }


@router.get("/stats/users")
async def get_user_stats(
        db: AsyncSession = Depends(get_db),
        _: User = Depends(deps.get_current_superuser),
) -> Any:
    """用户总数、活跃用户数、角色分布"""
    base = select(func.count()).select_from(User).where(User)
    total = await db.scalar(base)
    active = await db.scalar(base.where(User.is_active == True))

    role_stmt = (
        select(User.role, func.count())
        .where(User)
        .group_by(User.role)
    )
    role_rows = (await db.execute(role_stmt)).all()
    roles = {row[0]: row[1] for row in role_rows}

    return {
        "total_users": total,
        "active_users": active,
        "by_role": roles,
    }


@router.get("/stats/model-usage")
async def get_model_usage_stats(
        days: int = Query(7, ge=1, le=365),
        db: AsyncSession = Depends(get_db),
        _: User = Depends(deps.get_current_superuser),
) -> Any:
    """最近 N 天的模型调用次数、Token 消耗、费用"""
    since = datetime.utcnow() - timedelta(days=days)

    stmt = select(
        func.count().label("total_calls"),
        func.sum(ModelUsageLog.input_tokens).label("total_input_tokens"),
        func.sum(ModelUsageLog.output_tokens).label("total_output_tokens"),
        func.sum(ModelUsageLog.cost).label("total_cost"),
    ).where(
        and_(ModelUsageLog.created_at >= since, ModelUsageLog)
    )
    result = await db.execute(stmt)
    row = result.one()

    # 按请求类型分组
    type_stmt = (
        select(ModelUsageLog.request_type, func.count())
        .where(ModelUsageLog.created_at >= since)
        .group_by(ModelUsageLog.request_type)
    )
    type_rows = (await db.execute(type_stmt)).all()
    by_type = {row[0]: row[1] for row in type_rows}

    return {
        "period_days": days,
        "total_calls": row.total_calls,
        "total_input_tokens": row.total_input_tokens,
        "total_output_tokens": row.total_output_tokens,
        "total_cost": float(row.total_cost or 0),
        "by_request_type": by_type,
    }


@router.get("/stats/conversations")
async def get_conversation_stats(
        days: int = Query(7, ge=1, le=365),
        db: AsyncSession = Depends(get_db),
        _: User = Depends(deps.get_current_superuser),
) -> Any:
    """最近 N 天创建的会话数，按模式统计"""
    since = datetime.utcnow() - timedelta(days=days)

    total = await db.scalar(
        select(func.count()).select_from(Conversation).where(
            Conversation.created_at >= since, Conversation
        )
    )
    mode_stmt = (
        select(Conversation.mode, func.count())
        .where(Conversation.created_at >= since)
        .group_by(Conversation.mode)
    )
    mode_rows = (await db.execute(mode_stmt)).all()
    by_mode = {row[0]: row[1] for row in mode_rows}

    return {
        "period_days": days,
        "total_conversations": total,
        "by_mode": by_mode,
    }
