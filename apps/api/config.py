"""
API Configuration for DT-RAG v1.8.1

Configuration management for the DT-RAG API including environment-specific settings,
security configuration, rate limiting, and performance tuning.

This module integrates with the new environment management and LLM configuration systems
to provide comprehensive, secure, and fallback-enabled configuration management.
"""

import os
import secrets
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

# Import new configuration management modules
try:
    from .env_manager import get_env_manager, Environment
    from .llm_config import get_llm_config
except ImportError:
    # Fallback for direct execution
    from env_manager import get_env_manager, Environment
    from llm_config import get_llm_config

logger = logging.getLogger(__name__)

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
    url: str = "redis://redis:6379/0"
    max_connections: int = 10
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    socket_keepalive: bool = True

@dataclass
class SecurityConfig:
    """
    Security and authentication configuration

    SECURITY REQUIREMENTS:
    - secret_key MUST be loaded from environment variable in production
    - secret_key MUST be cryptographically random (min 256 bits)
    - NEVER use hardcoded secrets in production environments
    - JWT secrets should be rotated regularly in production
    """
    # This will be overridden by environment variable or generated securely
    secret_key: str = ""  # Will be set by _generate_secure_secret() if needed
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30
    jwt_refresh_expiration_days: int = 7
    password_min_length: int = 8
    password_require_special: bool = True
    api_key_header: str = "X-API-Key"
    oauth_providers: Dict[str, Dict[str, str]] = field(default_factory=dict)
    trusted_hosts: List[str] = field(default_factory=list)

def _generate_secure_secret() -> str:
    """
    Generate a cryptographically secure secret key for JWT signing

    Uses Python's secrets module to generate a URL-safe, base64-encoded
    random string with 256 bits of entropy (recommended for JWT secrets).

    Returns:
        str: A secure random secret key suitable for JWT signing

    Security Note:
        This should only be used in development/testing environments.
        Production environments MUST use the SECRET_KEY environment variable.
    """
    # Generate 32 random bytes (256 bits) and encode as URL-safe base64
    return secrets.token_urlsafe(32)

def _validate_secret_strength(secret: str) -> bool:
    """
    Validate the strength of a JWT secret key

    Args:
        secret: The secret key to validate

    Returns:
        bool: True if the secret meets security requirements

    Security Requirements:
        - Minimum length of 32 characters
        - Should not be a common/weak password
        - Should contain varied character types
    """
    if len(secret) < 32:
        return False

    # Check for obviously weak/default secrets
    weak_secrets = [
        "your-super-secret-key-change-in-production",
        "secret",
        "password",
        "123456",
        "change-me",
        "development-key"
    ]

    if secret.lower() in [weak.lower() for weak in weak_secrets]:
        return False

    return True

def _validate_openai_api_key(api_key: Optional[str]) -> bool:
    """
    Validate OpenAI API key format

    Args:
        api_key: The API key to validate

    Returns:
        bool: True if the key meets OpenAI format requirements

    Requirements:
        - Must start with 'sk-' prefix (standard) or 'sk-proj-' (project-scoped)
        - Minimum total length of 48 characters
        - None or empty strings are invalid
    """
    if not api_key:
        return False

    if not (api_key.startswith("sk-") or api_key.startswith("sk-proj-")):
        return False

    if len(api_key) < 48:
        return False

    return True

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
    redis_url: str = "redis://redis:6379/1"

@dataclass
class CORSConfig:
    """
    CORS configuration with security-first approach

    Security Guidelines:
    - Never use wildcard "*" for allow_origins in production
    - Only specify explicit, trusted origins
    - Use specific headers instead of wildcard for allow_headers
    - Enable credentials only when necessary and with specific origins
    """
    allow_origins: List[str] = field(default_factory=lambda: ["http://localhost:3000", "http://localhost:8080"])
    allow_credentials: bool = True
    allow_methods: List[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
    # Specific headers instead of wildcard for security
    allow_headers: List[str] = field(default_factory=lambda: [
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-API-Key",
        "X-Requested-With",
        "X-Request-ID",
        "Cache-Control"
    ])
    expose_headers: List[str] = field(default_factory=lambda: ["X-Request-ID", "X-RateLimit-Remaining", "X-RateLimit-Limit"])
    max_age: int = 86400  # 24 hours

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
    host: str = "0.0.0.0"  # nosec B104 - intentional for container deployment
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

    Integrates with the new environment management and LLM configuration systems
    to provide comprehensive, validated configuration.

    Returns:
        APIConfig instance with environment-specific settings
    """

    # Get environment manager and LLM config
    env_manager = get_env_manager()

    # Base configuration
    config = APIConfig()
    config.environment = env_manager.current_env.value
    config.debug = env_manager.config.debug
    config.testing = env_manager.config.testing

    # Database configuration from environment manager
    db_config = env_manager.get_database_config()
    config.database.url = db_config["url"]
    config.database.pool_size = db_config["pool_size"]
    config.database.max_overflow = db_config["max_overflow"]
    config.database.echo = db_config["echo"]

    # Additional database settings
    config.database.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    config.database.pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))

    # Redis configuration
    if redis_url := os.getenv("REDIS_URL"):
        config.redis.url = redis_url
        config.rate_limit.redis_url = redis_url + "/1"  # Use different DB for rate limiting

    # Security configuration - CRITICAL: JWT Secret Key Management
    secret_key = os.getenv("SECRET_KEY")

    if secret_key:
        # Validate the provided secret key strength
        if not _validate_secret_strength(secret_key):
            if config.environment == "production":
                raise ValueError(
                    "Provided SECRET_KEY does not meet security requirements. "
                    "Must be at least 32 characters and not use common/weak values."
                )
            else:
                # Log warning in non-production environments but continue
                print(f"WARNING: Weak SECRET_KEY detected in {config.environment} environment")

        config.security.secret_key = secret_key

    elif config.environment == "production":
        # Production MUST use environment variable
        raise ValueError(
            "SECRET_KEY environment variable is REQUIRED in production. "
            "Generate a secure secret using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )

    elif config.environment in ["development", "testing"]:
        # Generate secure secret for development/testing if not provided
        config.security.secret_key = _generate_secure_secret()
        print(f"INFO: Generated secure secret key for {config.environment} environment")

    else:
        # Staging and other environments should use environment variable
        raise ValueError(
            f"SECRET_KEY environment variable is required for {config.environment} environment"
        )

    config.security.jwt_expiration_minutes = int(os.getenv("JWT_EXPIRATION_MINUTES", "30"))
    config.security.jwt_refresh_expiration_days = int(os.getenv("JWT_REFRESH_EXPIRATION_DAYS", "7"))

    # CORS configuration - Environment specific security
    if cors_origins := os.getenv("CORS_ORIGINS"):
        origins = [origin.strip() for origin in cors_origins.split(",")]

        # Security validation: no wildcards in production
        if config.environment == "production":
            if "*" in origins:
                raise ValueError(
                    "Wildcard CORS origins are not allowed in production. "
                    "Please specify exact origins in CORS_ORIGINS environment variable."
                )
            # Ensure HTTPS in production
            for origin in origins:
                if origin.startswith("http://") and not origin.startswith("http://localhost"):
                    raise ValueError(
                        f"HTTP origins are not allowed in production: {origin}. "
                        "Please use HTTPS origins only."
                    )

        config.cors.allow_origins = origins

    # Additional CORS headers if specified
    if cors_headers := os.getenv("CORS_HEADERS"):
        headers = [header.strip() for header in cors_headers.split(",")]

        # Security validation: no wildcards
        if "*" in headers:
            if config.environment == "production":
                raise ValueError(
                    "Wildcard CORS headers are not allowed in production. "
                    "Please specify exact headers in CORS_HEADERS environment variable."
                )
            else:
                print(f"WARNING: Wildcard CORS headers detected in {config.environment} environment")

        config.cors.allow_headers = headers

    # CORS credentials configuration
    if cors_credentials := os.getenv("CORS_CREDENTIALS"):
        config.cors.allow_credentials = cors_credentials.lower() == "true"

        # Security warning: credentials with wildcard origins
        if config.cors.allow_credentials and "*" in config.cors.allow_origins:
            if config.environment == "production":
                raise ValueError(
                    "CORS credentials cannot be enabled with wildcard origins in production"
                )
            else:
                print(f"WARNING: CORS credentials with wildcard origins in {config.environment} environment")

    # Monitoring configuration
    config.monitoring.enabled = os.getenv("MONITORING_ENABLED", "true").lower() == "true"
    config.monitoring.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    config.monitoring.trace_sampling_rate = float(os.getenv("TRACE_SAMPLING_RATE", "0.1"))

    # Performance configuration
    config.performance.worker_processes = int(os.getenv("WORKER_PROCESSES", "1"))
    config.performance.worker_connections = int(os.getenv("WORKER_CONNECTIONS", "1000"))

    # Environment-specific overrides using new environment manager
    security_config = env_manager.get_security_config()
    feature_flags = env_manager.get_feature_flags()

    # Apply security configuration
    config.docs_url = "/docs" if security_config["enable_docs"] else None
    config.redoc_url = "/redoc" if security_config["enable_docs"] else None
    # Note: config.debug already set from env_manager.config.debug at line 266

    # Apply feature flags
    config.enable_swagger_ui = feature_flags["enable_swagger_ui"]
    config.enable_redoc = feature_flags["enable_redoc"]
    config.enable_metrics = feature_flags["enable_metrics"]
    config.enable_rate_limiting = feature_flags["enable_rate_limiting"]
    config.enable_request_logging = feature_flags["enable_request_logging"]
    config.enable_error_tracking = feature_flags["enable_error_tracking"]

    # Environment-specific settings
    if env_manager.current_env == Environment.PRODUCTION:
        config.allowed_hosts = ["api.dt-rag.com", "dt-rag.com"]

        # Secure production CORS settings (only if not overridden by env vars)
        if not os.getenv("CORS_ORIGINS"):
            config.cors.allow_origins = ["https://dt-rag.com", "https://app.dt-rag.com"]

        # More restrictive CORS in production
        config.cors.allow_credentials = True
        config.cors.max_age = 3600  # 1 hour cache for production

        config.monitoring.log_level = "WARNING"
        config.performance.worker_processes = env_manager.config.worker_processes

    elif env_manager.current_env == Environment.STAGING:
        config.allowed_hosts = ["staging-api.dt-rag.com"]

        # Staging CORS settings (only if not overridden by env vars)
        if not os.getenv("CORS_ORIGINS"):
            config.cors.allow_origins = ["https://staging.dt-rag.com", "https://staging-app.dt-rag.com"]

        config.cors.max_age = 1800  # 30 minutes cache for staging
        config.monitoring.log_level = "INFO"
        config.performance.worker_processes = env_manager.config.worker_processes

    elif env_manager.current_env == Environment.DEVELOPMENT:
        # Development allows more origins but still secure headers
        if not os.getenv("CORS_ORIGINS"):
            config.cors.allow_origins = [
                "http://localhost:3000",
                "http://localhost:3001",
                "http://localhost:8080",
                "http://localhost:8081",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8080"
            ]
        config.cors.max_age = 300  # 5 minutes cache for development
        config.performance.worker_processes = env_manager.config.worker_processes

    elif env_manager.current_env == Environment.TESTING:
        config.monitoring.enabled = False
        config.rate_limit.default_rate = "1000/minute"  # Higher limits for testing
        config.performance.worker_processes = 1

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
        # Validate secret key is secure and not default
        if not config.security.secret_key:
            raise ValueError("SECRET_KEY is required in production")

        if not _validate_secret_strength(config.security.secret_key):
            raise ValueError(
                "SECRET_KEY does not meet security requirements in production. "
                "Must be at least 32 characters and cryptographically secure."
            )

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

    # CORS validation
    if config.environment == "production":
        # Validate no wildcard origins in production
        if "*" in config.cors.allow_origins:
            raise ValueError("Wildcard CORS origins are not allowed in production")

        # Validate HTTPS origins in production (except localhost for testing)
        for origin in config.cors.allow_origins:
            if origin.startswith("http://") and not origin.startswith("http://localhost"):
                raise ValueError(f"HTTP origin not allowed in production: {origin}")

        # Validate no wildcard headers in production
        if "*" in config.cors.allow_headers:
            raise ValueError("Wildcard CORS headers are not allowed in production")

        # Validate credentials with specific origins
        if config.cors.allow_credentials and "*" in config.cors.allow_origins:
            raise ValueError("CORS credentials cannot be enabled with wildcard origins")

def get_security_info() -> Dict[str, Any]:
    """
    Get security configuration information for administrative purposes

    Returns:
        Dict containing non-sensitive security configuration details

    Note:
        This function does NOT return actual secret keys for security reasons.
        It only provides metadata about the security configuration.
    """
    config = get_api_config()
    env_manager = get_env_manager()

    return {
        "environment": config.environment,
        "jwt_algorithm": config.security.jwt_algorithm,
        "jwt_expiration_minutes": config.security.jwt_expiration_minutes,
        "jwt_refresh_expiration_days": config.security.jwt_refresh_expiration_days,
        "password_min_length": config.security.password_min_length,
        "password_require_special": config.security.password_require_special,
        "api_key_header": config.security.api_key_header,
        "secret_key_configured": bool(config.security.secret_key),
        "secret_key_length": len(config.security.secret_key) if config.security.secret_key else 0,
        "secret_key_is_secure": _validate_secret_strength(config.security.secret_key) if config.security.secret_key else False,
        "security_recommendations": _get_security_recommendations(config),
        "environment_validation": env_manager.validate_environment()
    }

def get_system_status() -> Dict[str, Any]:
    """
    Get comprehensive system status including environment, LLM services, and configuration

    Returns:
        Dict containing complete system status information
    """
    env_manager = get_env_manager()
    llm_config_manager = get_llm_config()

    return {
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        "environment": env_manager.get_environment_summary(),
        "llm_services": llm_config_manager.get_service_status(),
        "configuration": {
            "database_type": "sqlite" if "sqlite" in os.getenv("DATABASE_URL", "") else "postgresql",
            "redis_enabled": bool(os.getenv("REDIS_URL")),
            "monitoring_enabled": os.getenv("MONITORING_ENABLED", "true").lower() == "true",
            "debug_mode": os.getenv("DEBUG", "false").lower() == "true"
        },
        "api_keys": {
            "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
            "anthropic_configured": bool(os.getenv("ANTHROPIC_API_KEY")),
            "azure_configured": bool(os.getenv("AZURE_OPENAI_API_KEY"))
        },
        "system_health": {
            "configuration_valid": env_manager.validate_environment()["is_valid"],
            "llm_service_available": llm_config_manager.get_service_status()["system_operational"],
            "fallback_enabled": True
        }
    }

def get_configuration_recommendations() -> List[str]:
    """
    Get configuration recommendations based on current environment and setup

    Returns:
        List of actionable configuration recommendations
    """
    env_manager = get_env_manager()
    llm_config_manager = get_llm_config()

    recommendations = []

    # Environment validation recommendations
    env_validation = env_manager.validate_environment()
    recommendations.extend(env_validation.get("recommendations", []))

    # LLM service recommendations
    llm_status = llm_config_manager.get_service_status()

    if llm_status["llm_service"]["is_dummy"]:
        recommendations.append("Configure LLM API keys for production AI responses")

    if llm_status["embedding_service"]["is_dummy"]:
        recommendations.append("Configure embedding API keys for semantic search")

    # Database recommendations
    if "sqlite" in os.getenv("DATABASE_URL", ""):
        if env_manager.current_env == Environment.PRODUCTION:
            recommendations.append("Use PostgreSQL for production instead of SQLite")
        else:
            recommendations.append("Consider PostgreSQL for better performance and features")

    # Redis recommendations
    if not os.getenv("REDIS_URL"):
        recommendations.append("Configure Redis for improved caching and rate limiting")

    # Security recommendations
    if env_manager.current_env == Environment.PRODUCTION:
        if not os.getenv("SECRET_KEY"):
            recommendations.append("Set a strong SECRET_KEY environment variable")

        cors_origins = os.getenv("CORS_ORIGINS", "")
        if "*" in cors_origins:
            recommendations.append("Replace wildcard CORS origins with specific trusted domains")

    return recommendations

def _get_security_recommendations(config: APIConfig) -> List[str]:
    """
    Generate security recommendations based on current configuration

    Args:
        config: The API configuration to analyze

    Returns:
        List of security recommendations
    """
    recommendations = []

    if config.environment == "production":
        if config.debug:
            recommendations.append("Disable debug mode in production")

        if config.docs_url or config.redoc_url:
            recommendations.append("Disable API documentation in production")

        if not config.security.secret_key or not _validate_secret_strength(config.security.secret_key):
            recommendations.append("Use a strong SECRET_KEY (32+ characters, cryptographically random)")

    if config.security.jwt_expiration_minutes > 60:
        recommendations.append("Consider shorter JWT expiration time for better security")

    if config.security.password_min_length < 12:
        recommendations.append("Consider increasing minimum password length to 12+ characters")

    if not config.security.password_require_special:
        recommendations.append("Consider requiring special characters in passwords")

    # CORS security recommendations
    if "*" in config.cors.allow_origins:
        recommendations.append("Replace wildcard CORS origins with specific trusted origins")

    if "*" in config.cors.allow_headers:
        recommendations.append("Replace wildcard CORS headers with specific required headers")

    if config.cors.allow_credentials and len(config.cors.allow_origins) > 5:
        recommendations.append("Consider limiting CORS origins when credentials are enabled")

    # Check for HTTP origins in non-development environments
    if config.environment not in ["development", "testing"]:
        http_origins = [origin for origin in config.cors.allow_origins
                       if origin.startswith("http://") and not origin.startswith("http://localhost")]
        if http_origins:
            recommendations.append(f"Use HTTPS for these origins: {', '.join(http_origins)}")

    return recommendations

# Alias for backwards compatibility
get_config = get_api_config

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
    "get_config",  # Alias for backwards compatibility
    "get_openapi_tags",
    "validate_config",
    "get_security_info",
    "get_system_status",
    "get_configuration_recommendations",
    "_generate_secure_secret",
    "_validate_secret_strength",
    "_validate_openai_api_key"
]