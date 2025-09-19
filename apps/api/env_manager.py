"""
Environment Configuration Manager
Handles environment-specific configurations and validation for DT-RAG v1.8.1
"""

import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

class Environment(str, Enum):
    """Supported environment types"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class EnvironmentConfig:
    """Environment-specific configuration"""
    name: Environment
    database_url: str
    debug: bool = False
    testing: bool = False

    # Security settings
    require_https: bool = False
    strict_cors: bool = False

    # Feature flags
    enable_docs: bool = True
    enable_debug_logging: bool = True
    enable_experimental_features: bool = True

    # Performance settings
    worker_processes: int = 1
    connection_pool_size: int = 5

class EnvironmentManager:
    """
    Manages environment-specific configurations and validations
    """

    def __init__(self):
        self.current_env = self._detect_environment()
        self.config = self._load_environment_config()
        self._validation_results: Optional[Dict[str, Any]] = None

    def _detect_environment(self) -> Environment:
        """Detect current environment from environment variables"""
        env_name = os.getenv("DT_RAG_ENV", "development").lower()

        try:
            return Environment(env_name)
        except ValueError:
            logger.warning(f"Unknown environment '{env_name}', defaulting to development")
            return Environment.DEVELOPMENT

    def _load_environment_config(self) -> EnvironmentConfig:
        """Load configuration for the current environment"""
        config = EnvironmentConfig(
            name=self.current_env,
            database_url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./dt_rag_test.db")
        )

        # Environment-specific settings
        if self.current_env == Environment.PRODUCTION:
            config.debug = False
            config.testing = False
            config.require_https = True
            config.strict_cors = True
            config.enable_docs = False
            config.enable_debug_logging = False
            config.enable_experimental_features = False
            config.worker_processes = int(os.getenv("WORKER_PROCESSES", "4"))
            config.connection_pool_size = int(os.getenv("DB_POOL_SIZE", "20"))

        elif self.current_env == Environment.STAGING:
            config.debug = False
            config.testing = False
            config.require_https = True
            config.strict_cors = True
            config.enable_docs = True
            config.enable_debug_logging = True
            config.enable_experimental_features = False
            config.worker_processes = int(os.getenv("WORKER_PROCESSES", "2"))
            config.connection_pool_size = int(os.getenv("DB_POOL_SIZE", "10"))

        elif self.current_env == Environment.TESTING:
            config.debug = os.getenv("DEBUG", "true").lower() == "true"
            config.testing = True
            config.require_https = False
            config.strict_cors = False
            config.enable_docs = True
            config.enable_debug_logging = True
            config.enable_experimental_features = True
            config.worker_processes = 1
            config.connection_pool_size = int(os.getenv("DB_POOL_SIZE", "5"))

        else:  # DEVELOPMENT
            config.debug = os.getenv("DEBUG", "true").lower() == "true"
            config.testing = False
            config.require_https = False
            config.strict_cors = False
            config.enable_docs = True
            config.enable_debug_logging = True
            config.enable_experimental_features = True
            config.worker_processes = 1
            config.connection_pool_size = int(os.getenv("DB_POOL_SIZE", "5"))

        return config

    def validate_environment(self) -> Dict[str, Any]:
        """
        Validate current environment configuration

        Returns:
            Dict containing validation results
        """
        if self._validation_results is not None:
            return self._validation_results

        results = {
            "environment": self.current_env.value,
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "recommendations": [],
            "checks": {}
        }

        # Database validation
        db_check = self._validate_database()
        results["checks"]["database"] = db_check
        if not db_check["is_valid"]:
            results["is_valid"] = False
            results["errors"].extend(db_check["errors"])

        # Security validation
        security_check = self._validate_security()
        results["checks"]["security"] = security_check
        results["warnings"].extend(security_check["warnings"])
        results["recommendations"].extend(security_check["recommendations"])

        # Required environment variables
        env_vars_check = self._validate_required_env_vars()
        results["checks"]["environment_variables"] = env_vars_check
        if not env_vars_check["is_valid"]:
            results["warnings"].extend(env_vars_check["warnings"])

        # API services validation
        api_check = self._validate_api_services()
        results["checks"]["api_services"] = api_check
        results["warnings"].extend(api_check["warnings"])

        # Performance validation
        perf_check = self._validate_performance_settings()
        results["checks"]["performance"] = perf_check
        results["recommendations"].extend(perf_check["recommendations"])

        self._validation_results = results
        return results

    def _validate_database(self) -> Dict[str, Any]:
        """Validate database configuration"""
        result = {
            "is_valid": True,
            "database_url": self.config.database_url,
            "database_type": "unknown",
            "errors": [],
            "warnings": []
        }

        db_url = self.config.database_url.lower()

        if "sqlite" in db_url:
            result["database_type"] = "sqlite"
            result["warnings"].append("Using SQLite - suitable for testing but not for production")

            # Check if file exists for SQLite
            if ":///" in db_url:
                db_path = db_url.split("///")[1]
                if not Path(db_path).parent.exists():
                    result["errors"].append(f"Database directory does not exist: {Path(db_path).parent}")
                    result["is_valid"] = False

        elif "postgresql" in db_url:
            result["database_type"] = "postgresql"
            if self.current_env == Environment.PRODUCTION:
                result["warnings"].append("Ensure PostgreSQL is properly configured for production")

        else:
            result["errors"].append(f"Unsupported database type in URL: {self.config.database_url}")
            result["is_valid"] = False

        return result

    def _validate_security(self) -> Dict[str, Any]:
        """Validate security configuration"""
        result = {
            "warnings": [],
            "recommendations": []
        }

        # Check SECRET_KEY
        secret_key = os.getenv("SECRET_KEY")
        if not secret_key:
            if self.current_env == Environment.PRODUCTION:
                result["warnings"].append("SECRET_KEY not set - required for production")
            else:
                result["warnings"].append("SECRET_KEY not set - will be auto-generated")
        elif len(secret_key) < 32:
            result["warnings"].append("SECRET_KEY is too short - should be at least 32 characters")

        # Check HTTPS requirements
        if self.config.require_https:
            cors_origins = os.getenv("CORS_ORIGINS", "")
            if "http://" in cors_origins and "localhost" not in cors_origins:
                result["warnings"].append("HTTP origins detected in production environment")

        # Check CORS configuration
        if self.current_env == Environment.PRODUCTION:
            cors_origins = os.getenv("CORS_ORIGINS", "")
            if "*" in cors_origins:
                result["warnings"].append("Wildcard CORS origins not recommended for production")

        # Recommendations
        if self.current_env == Environment.PRODUCTION:
            result["recommendations"].extend([
                "Use environment variables for all secrets",
                "Enable HTTPS and strict CORS policies",
                "Disable debug mode and API documentation",
                "Use strong, randomly generated SECRET_KEY"
            ])

        return result

    def _validate_required_env_vars(self) -> Dict[str, Any]:
        """Validate required environment variables"""
        result = {
            "is_valid": True,
            "missing": [],
            "warnings": []
        }

        # Environment-specific required variables
        required_vars = {
            Environment.PRODUCTION: [
                "SECRET_KEY",
                "DATABASE_URL"
            ],
            Environment.STAGING: [
                "DATABASE_URL"
            ],
            Environment.TESTING: [
                "DATABASE_URL"
            ],
            Environment.DEVELOPMENT: []
        }

        # Optional but recommended variables
        recommended_vars = [
            "OPENAI_API_KEY",
            "REDIS_URL"
        ]

        required = required_vars.get(self.current_env, [])
        for var in required:
            if not os.getenv(var):
                result["missing"].append(var)
                result["is_valid"] = False

        # Check recommended variables
        for var in recommended_vars:
            if not os.getenv(var):
                result["warnings"].append(f"Recommended environment variable not set: {var}")

        return result

    def _validate_api_services(self) -> Dict[str, Any]:
        """Validate API services configuration"""
        result = {
            "warnings": [],
            "services": {}
        }

        # Check LLM service configuration
        llm_mode = os.getenv("LLM_SERVICE_MODE", "dummy")
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        azure_key = os.getenv("AZURE_OPENAI_API_KEY")

        result["services"]["llm"] = {
            "mode": llm_mode,
            "has_openai_key": bool(openai_key),
            "has_anthropic_key": bool(anthropic_key),
            "has_azure_key": bool(azure_key)
        }

        if llm_mode == "dummy":
            result["warnings"].append("LLM service in dummy mode - no real AI responses will be generated")
        elif llm_mode == "openai" and not openai_key:
            result["warnings"].append("OpenAI mode selected but no API key configured")
        elif llm_mode == "anthropic" and not anthropic_key:
            result["warnings"].append("Anthropic mode selected but no API key configured")
        elif llm_mode == "azure" and not azure_key:
            result["warnings"].append("Azure mode selected but no API key configured")

        # Check embedding service
        embedding_mode = os.getenv("EMBEDDING_SERVICE_MODE", "dummy")
        result["services"]["embedding"] = {
            "mode": embedding_mode,
            "has_api_key": bool(openai_key or azure_key)
        }

        if embedding_mode == "dummy":
            result["warnings"].append("Embedding service in dummy mode - random vectors will be used")

        return result

    def _validate_performance_settings(self) -> Dict[str, Any]:
        """Validate performance configuration"""
        result = {
            "recommendations": [],
            "settings": {}
        }

        worker_processes = int(os.getenv("WORKER_PROCESSES", "1"))
        db_pool_size = int(os.getenv("DB_POOL_SIZE", "5"))

        result["settings"] = {
            "worker_processes": worker_processes,
            "db_pool_size": db_pool_size
        }

        # Environment-specific recommendations
        if self.current_env == Environment.PRODUCTION:
            if worker_processes < 2:
                result["recommendations"].append("Consider using multiple worker processes for production")
            if db_pool_size < 10:
                result["recommendations"].append("Consider increasing database pool size for production")

        return result

    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration for the current environment"""
        return {
            "url": self.config.database_url,
            "pool_size": self.config.connection_pool_size,
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
            "echo": self.config.enable_debug_logging and self.config.debug,
            "echo_pool": os.getenv("DB_ECHO_POOL", "false").lower() == "true"
        }

    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration for the current environment"""
        return {
            "require_https": self.config.require_https,
            "strict_cors": self.config.strict_cors,
            "debug": self.config.debug,
            "enable_docs": self.config.enable_docs
        }

    def get_feature_flags(self) -> Dict[str, bool]:
        """Get feature flags for the current environment"""
        return {
            "enable_swagger_ui": self.config.enable_docs,
            "enable_redoc": self.config.enable_docs,
            "enable_experimental_features": self.config.enable_experimental_features,
            "enable_debug_logging": self.config.enable_debug_logging,
            "enable_metrics": os.getenv("ENABLE_METRICS", "true").lower() == "true",
            "enable_rate_limiting": os.getenv("ENABLE_RATE_LIMITING", "false").lower() == "true"
        }

    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.current_env == Environment.PRODUCTION

    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.current_env == Environment.DEVELOPMENT

    def is_testing(self) -> bool:
        """Check if running in testing environment"""
        return self.current_env == Environment.TESTING

    def get_environment_summary(self) -> Dict[str, Any]:
        """Get comprehensive environment summary"""
        validation = self.validate_environment()

        return {
            "environment": self.current_env.value,
            "config": {
                "debug": self.config.debug,
                "testing": self.config.testing,
                "database_type": validation["checks"]["database"]["database_type"],
                "worker_processes": self.config.worker_processes
            },
            "validation": {
                "is_valid": validation["is_valid"],
                "error_count": len(validation["errors"]),
                "warning_count": len(validation["warnings"]),
                "recommendation_count": len(validation["recommendations"])
            },
            "services": validation["checks"]["api_services"]["services"],
            "security": {
                "require_https": self.config.require_https,
                "strict_cors": self.config.strict_cors
            },
            "features": self.get_feature_flags()
        }

# Global instance
_env_manager: Optional[EnvironmentManager] = None

def get_env_manager() -> EnvironmentManager:
    """Get global environment manager instance"""
    global _env_manager
    if _env_manager is None:
        _env_manager = EnvironmentManager()
    return _env_manager

def get_current_environment() -> Environment:
    """Get current environment"""
    return get_env_manager().current_env

def validate_current_environment() -> Dict[str, Any]:
    """Validate current environment configuration"""
    return get_env_manager().validate_environment()

def is_production() -> bool:
    """Check if running in production"""
    return get_env_manager().is_production()

def is_development() -> bool:
    """Check if running in development"""
    return get_env_manager().is_development()

def is_testing() -> bool:
    """Check if running in testing"""
    return get_env_manager().is_testing()

__all__ = [
    "Environment",
    "EnvironmentConfig",
    "EnvironmentManager",
    "get_env_manager",
    "get_current_environment",
    "validate_current_environment",
    "is_production",
    "is_development",
    "is_testing"
]