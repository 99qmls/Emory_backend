# app/services/tasks/notification_tasks.py
from app.core.celery_app import celery_app
from app.utils.logger import logger

@celery_app.task(name="send_email_notification")
def send_email_notification(user_id: str, subject: str, body: str):
    """
    发送邮件通知（待实现）
    后续可接入 smtplib / 第三方邮件服务
    """
    logger.info(f"[占位] 向用户 {user_id} 发送邮件：{subject}")
    # TODO: 实现真正的邮件发送逻辑

@celery_app.task(name="send_system_notification")
def send_system_notification(user_id: str, message: str, level: str = "info"):
    """
    系统内部通知（待实现）
    可写入数据库通知表或通过 WebSocket 推送
    """
    logger.info(f"[占位] 系统通知 {user_id}：{message}")
    # TODO: 实现通知写入与推送