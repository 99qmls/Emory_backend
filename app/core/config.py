# app/core/config.py

from typing import Optional

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict
)


class Settings(BaseSettings):

    # ==================================================
    # 应用
    # ==================================================

    SECRET_KEY: str

    DEBUG: bool = False

    # ==================================================
    # 数据库
    # ==================================================

    DATABASE_URL: str = (
        "mysql+asyncmy://emory:emory123@localhost:3306/emory_db"
    )

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ==================================================
    # Redis
    # ==================================================

    REDIS_URL: str = (
        "redis://localhost:6379/0"
    )

    # ==================================================
    # MinIO
    # ==================================================

    MINIO_ENDPOINT: str = "localhost:9000"

    MINIO_ACCESS_KEY: str = "minioadmin"

    MINIO_SECRET_KEY: str = "minioadmin"

    MINIO_BUCKET: str = "emory-documents"

    # ==================================================
    # JWT
    # ==================================================

    ALGORITHM: str = "HS256"

    # ==================================================
    # LLM
    # ==================================================

    DEFAULT_LLM_MODEL: str = (
        "ollama:deepseek-r1:7b"
    )

    OLLAMA_BASE_URL: str = (
        "http://localhost:11434"
    )

    OLLAMA_HOST: str = (
        "http://localhost:11434"
    )

    OPENAI_API_KEY: Optional[str] = None

    OPENAI_BASE_URL: str = (
        "https://api.deepseek.com/v1"
    )

    # ==================================================
    # Chroma
    # ==================================================

    CHROMA_PERSIST_DIR: str = "./chroma_data"

    # ==================================================
    # Embedding
    # ==================================================

    EMBEDDING_MODEL_NAME: str = "m3e"

    # ==================================================
    # Rerank
    # ==================================================

    USE_RERANK: bool = True

    RERANKER_MODEL_NAME: str = (
        "BAAI/bge-reranker-v2-m3"
    )

    # ==================================================
    # Emotion
    # ==================================================

    EMOTION_ANALYZER_MODEL: str = (
        "ollama:deepseek-r1:7b"
    )

    # ==================================================
    # 高德地图
    # ==================================================

    GAODE_MAPS_API_KEY: Optional[str] = None

    # ==================================================
    # Celery
    # ==================================================

    CELERY_WORKER_CONCURRENCY: int = 4

    # ==================================================
    # MCP
    # ==================================================

    MCP_WEATHER_URL: str = (
        "http://127.0.0.1:7001/mcp"
    )

    MCP_MAX_CONNECTIONS: int = 20

    MCP_MAX_KEEPALIVE: int = 10

    # ==================================================
    # Pydantic Settings
    # ==================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()