"""
Application Settings

Centralized configuration management using Pydantic.

@CODE:CLEAN-ARCHITECTURE-SETTINGS
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application Settings

    All configuration values with sensible defaults.
    Can be overridden via environment variables.
    """

    # Application
    app_name: str = "DT-RAG API"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/dt_rag"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_echo: bool = False

    # Redis (optional caching)
    redis_url: Optional[str] = None
    cache_ttl: int = 3600

    # Search
    search_default_top_k: int = 5
    search_bm25_topk: int = 50
    search_vector_topk: int = 50
    search_rerank_candidates: int = 100
    search_enable_reranking: bool = True

    # Embeddings
    embedding_model: str = "text-embedding-ada-002"
    embedding_dimension: int = 1536
    embedding_batch_size: int = 100

    # OpenAI
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    openai_temperature: float = 0.7

    # Security
    api_key: Optional[str] = None
    cors_origins: str = "*"
    rate_limit_requests: int = 100
    rate_limit_window: int = 60

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: Application settings
    """
    return Settings()
