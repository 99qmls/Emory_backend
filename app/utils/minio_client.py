# app/utils/minio_client.py
"""
MinIO 客户端封装（线程安全，支持自动创建桶）
"""
from minio import Minio
from minio.error import S3Error
from app.core.config import settings
from app.utils.logger import logger

# 创建 MinIO 客户端（全局单例）
minio_client = Minio(
    endpoint=settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=False,  # 开发环境 HTTP，生产应改为 True
)


def ensure_bucket_exists(bucket_name: str = None):
    """确保存储桶存在，不存在则创建"""
    name = bucket_name or settings.MINIO_BUCKET
    try:
        if not minio_client.bucket_exists(name):
            minio_client.make_bucket(name)
            logger.info(f"MinIO 存储桶 '{name}' 已创建")
        else:
            logger.debug(f"MinIO 存储桶 '{name}' 已存在")
    except S3Error as e:
        logger.error(f"MinIO 操作失败: {e}")
        raise


# 应用启动时自动执行一次
ensure_bucket_exists()
