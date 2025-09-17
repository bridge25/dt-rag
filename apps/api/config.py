"""
API Configuration for DT-RAG v1.8.1

Configuration management for the DT-RAG API including environment-specific settings,
security configuration, rate limiting, and performance tuning.
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str = "postgresql://localhost:5432/dt_rag"
    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False

@dataclass
class RedisConfig:
    """Redis configuration for caching and rate limiting"""
    url: str = "redis://localhost:6379/0"
    max_connections: int = 10
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    socket_keepalive: bool = True

@dataclass
class SecurityConfig:
    """Security and authentication configuration"""
    secret_key: str = "your-super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30
    jwt_refresh_expiration_days: int = 7
    password_min_length: int = 8
    password_require_special: bool = True
    api_key_header: str = "X-API-Key"
    oauth_providers: Dict[str, Dict[str, str]] = field(default_factory=dict)

@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    default_rate: str = "100/minute"
    burst_rate: str = "200/minute"
    auth_rate: str = "5/minute"
    search_rate: str = "50/minute"
    classification_rate: str = "30/minute"
    pipeline_rate: str = "10/minute"
    admin_rate: str = "1000/minute"
    redis_url: str = "redis://localhost:6379/1"

@dataclass
class CORSConfig:
    """CORS configuration"""
    allow_origins: List[str] = field(default_factory=lambda: ["http://localhost:3000", "http://localhost:8080"])
    allow_credentials: bool = True
    allow_methods: List[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
    allow_headers: List[str] = field(default_factory=lambda: ["*"])
    expose_headers: List[str] = field(default_factory=lambda: ["X-Request-ID", "X-RateLimit-*"])

@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration"""
    enabled: bool = True
    metrics_endpoint: str = "/metrics"
    prometheus_port: int = 8001
    trace_sampling_rate: float = 0.1
    log_level: str = "INFO"
    log_format: str = "json"
    request_logging: bool = True
    error_tracking: bool = True

@dataclass
class PerformanceConfig:
    """Performance optimization configuration"""
    worker_processes: int = 1
    worker_connections: int = 1000
    keepalive_timeout: int = 65
    max_requests: int = 1000
    max_requests_jitter: int = 100
    timeout_keep_alive: int = 5
    timeout_graceful_shutdown: int = 30

@dataclass
class APIConfig:
    """Main API configuration"""
    # Environment
    environment: str = "development"
    debug: bool = True
    testing: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    title: str = "Dynamic Taxonomy RAG API"
    version: str = "1.8.1"

    # Paths
    docs_url: Optional[str] = "/docs"
    redoc_url: Optional[str] = "/redoc"
    openapi_url: str = "/openapi.json"

    # Security
    allowed_hosts: List[str] = field(default_factory=lambda: ["*"])
    trusted_hosts: List[str] = field(default_factory=lambda: ["localhost", "127.0.0.1"])

    # Components
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    cors: CORSConfig = field(default_factory=CORSConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)

    # Feature flags
    enable_swagger_ui: bool = True
    enable_redoc: bool = True
    enable_metrics: bool = True
    enable_rate_limiting: bool = True
    enable_request_logging: bool = True
    enable_error_tracking: bool = True

def get_api_config() -> APIConfig:
    """
    Load API configuration from environment variables and defaults

    Returns:
        APIConfig instance with environment-specific settings
    """

    # Determine environment
    environment = os.getenv("DT_RAG_ENV", "development").lower()

    # Base configuration
    config = APIConfig()
    config.environment = environment
    config.debug = environment != "production"

    # Database configuration
    if db_url := os.getenv("DATABASE_URL"):
        config.database.url = db_url

    config.database.pool_size = int(os.getenv("DB_POOL_SIZE", "20"))
    config.database.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "30"))
    config.database.echo = os.getenv("DB_ECHO", "false").lower() == "true"

    # Redis configuration
    if redis_url := os.getenv("REDIS_URL"):
        config.redis.url = redis_url
        config.rate_limit.redis_url = redis_url + "/1"  # Use different DB for rate limiting

    # Security configuration
    if secret_key := os.getenv("SECRET_KEY"):
        config.security.secret_key = secret_key
    elif environment == "production":
        raise ValueError("SECRET_KEY environment variable is required in production")

    config.security.jwt_expiration_minutes = int(os.getenv("JWT_EXPIRATION_MINUTES", "30"))
    config.security.jwt_refresh_expiration_days = int(os.getenv("JWT_REFRESH_EXPIRATION_DAYS", "7"))

    # CORS configuration
    if cors_origins := os.getenv("CORS_ORIGINS"):
        config.cors.allow_origins = [origin.strip() for origin in cors_origins.split(",")]

    # Monitoring configuration
    config.monitoring.enabled = os.getenv("MONITORING_ENABLED", "true").lower() == "true"
    config.monitoring.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    config.monitoring.trace_sampling_rate = float(os.getenv("TRACE_SAMPLING_RATE", "0.1"))

    # Performance configuration
    config.performance.worker_processes = int(os.getenv("WORKER_PROCESSES", "1"))
    config.performance.worker_connections = int(os.getenv("WORKER_CONNECTIONS", "1000"))

    # Environment-specific overrides
    if environment == "production":
        config.docs_url = None  # Disable docs in production
        config.redoc_url = None
        config.debug = False
        config.allowed_hosts = ["api.dt-rag.com", "dt-rag.com"]
        config.cors.allow_origins = ["https://dt-rag.com", "https://app.dt-rag.com"]
        config.monitoring.log_level = "WARNING"
        config.performance.worker_processes = int(os.getenv("WORKER_PROCESSES", "4"))

    elif environment == "staging":
        config.allowed_hosts = ["staging-api.dt-rag.com"]
        config.cors.allow_origins = ["https://staging.dt-rag.com"]
        config.monitoring.log_level = "INFO"

    elif environment == "testing":
        config.testing = True
        config.database.echo = False
        config.monitoring.enabled = False
        config.rate_limit.default_rate = "1000/minute"  # Higher limits for testing

    return config

def get_openapi_tags() -> List[Dict[str, str]]:
    """
    Get OpenAPI tags for API documentation

    Returns:
        List of tag definitions for OpenAPI documentation
    """

    return [
        {
            "name": "Authentication",
            "description": "User authentication and session management"
        },
        {
            "name": "Taxonomy",
            "description": "Hierarchical taxonomy management and navigation"
        },
        {
            "name": "Search",
            "description": "Hybrid search operations with BM25 and vector search"
        },
        {
            "name": "Classification",
            "description": "Document classification with HITL support"
        },
        {
            "name": "Ingestion",
            "description": "Document ingestion and processing pipeline"
        },
        {
            "name": "Orchestration",
            "description": "LangGraph-based RAG pipeline execution"
        },
        {
            "name": "Evaluation",
            "description": "RAGAS evaluation and A/B testing framework"
        },
        {
            "name": "Monitoring",
            "description": "System metrics and observability"
        },
        {
            "name": "Security",
            "description": "Security management and compliance"
        },
        {
            "name": "Agent Factory",
            "description": "Dynamic agent creation and management"
        },
        {
            "name": "System",
            "description": "System health and status endpoints"
        }
    ]

# Configuration validation
def validate_config(config: APIConfig) -> None:
    """
    Validate API configuration

    Args:
        config: APIConfig instance to validate

    Raises:
        ValueError: If configuration is invalid
    """

    # Environment validation
    if config.environment not in ["development", "staging", "production", "testing"]:
        raise ValueError(f"Invalid environment: {config.environment}")

    # Security validation
    if config.environment == "production":
        if config.security.secret_key == "your-super-secret-key-change-in-production":
            raise ValueError("SECRET_KEY must be changed in production")

        if config.debug:
            raise ValueError("Debug mode must be disabled in production")

        if config.docs_url or config.redoc_url:
            raise ValueError("API documentation should be disabled in production")

    # Database validation
    if not config.database.url:
        raise ValueError("Database URL is required")

    # Rate limiting validation
    if config.enable_rate_limiting and not config.redis.url:
        raise ValueError("Redis URL is required when rate limiting is enabled")

    # Performance validation
    if config.performance.worker_processes < 1:
        raise ValueError("Worker processes must be at least 1")

    if config.performance.worker_connections < 100:
        raise ValueError("Worker connections must be at least 100")

# Export main configuration
__all__ = [
    "APIConfig",
    "DatabaseConfig",
    "RedisConfig",
    "SecurityConfig",
    "RateLimitConfig",
    "CORSConfig",
    "MonitoringConfig",
    "PerformanceConfig",
    "get_api_config",
    "get_openapi_tags",
    "validate_config"
]