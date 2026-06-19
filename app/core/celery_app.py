# ==============================================
# app/core/celery_app.py
# Celery 应用配置，用于异步任务（文档处理、通知等）
# ==============================================
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "emory",
    broker=settings.REDIS_URL,  # 使用 Redis 作为消息代理
    backend=settings.REDIS_URL,  # 结果也存入 Redis（便于追踪任务状态）
    include=[
        "app.services.tasks.document_tasks",
        "app.services.tasks.notification_tasks",
    ],
)

# 统一配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # 自动重试连接 Redis，提高系统韧性
    broker_connection_retry_on_startup=True,
    task_track_started=True,
    task_acks_late=True,  # 任务执行完成后才确认，避免丢失
    worker_prefetch_multiplier=1,  # 适合耗时较长的文档处理任务
)
