"""
Environment Manager for Norade v1.8.1

Handles environment-specific configuration management including environment detection,
database configuration, security settings, and feature flags.

@CODE:API-001
"""

import os
import logging
from typing import Dict, Any, List, TypedDict
from enum import Enum
from dataclasses import dataclass


logger = logging.getLogger(__name__)


class ValidationResult(TypedDict):
    """Type definition for validation results"""

    is_valid: bool
    warnings: List[str]
    errors: List[str]
    recommendations: List[str]


class Environment(Enum):
    """Environment types"""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class EnvironmentConfig:
    """Environment-specific configuration"""

    debug: bool = True
    testing: bool = False
    worker_processes: int = 1
    log_level: str = "INFO"
    enable_docs: bool = True


class EnvironmentManager:
    """Manages environment-specific configuration and validation"""

    def __init__(self) -> None:
        self.current_env = self._detect_environment()
        self.config = self._get_environment_config()

    def _detect_environment(self) -> Environment:
        """Detect current environment from environment variables"""
        env_name = os.getenv("ENVIRONMENT", "development").lower()

        try:
            return Environment(env_name)
        except ValueError:
            logger.warning(
                f"Unknown environment '{env_name}', defaulting to development"
            )
            return Environment.DEVELOPMENT

    def _get_environment_config(self) -> EnvironmentConfig:
        """Get configuration for current environment"""
        configs = {
            Environment.DEVELOPMENT: EnvironmentConfig(
                debug=True,
                testing=False,
                worker_processes=1,
                log_level="DEBUG",
                enable_docs=True,
            ),
            Environment.TESTING: EnvironmentConfig(
                debug=True,
                testing=True,
                worker_processes=1,
                log_level="DEBUG",
                enable_docs=True,
            ),
            Environment.STAGING: EnvironmentConfig(
                debug=False,
                testing=False,
                worker_processes=4,
                log_level="INFO",
                enable_docs=True,
            ),
            Environment.PRODUCTION: EnvironmentConfig(
                debug=False,
                testing=False,
                worker_processes=8,
                log_level="WARNING",
                enable_docs=False,
            ),
        }

        return configs.get(self.current_env, configs[Environment.DEVELOPMENT])

    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration for current environment"""
        database_url = os.getenv("DATABASE_URL", "sqlite:///./norade.db")

        config = {
            "url": database_url,
            "pool_size": int(os.getenv("DB_POOL_SIZE", "20")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "30")),
            "echo": self.current_env in [Environment.DEVELOPMENT, Environment.TESTING],
        }

        # Environment-specific overrides
        if self.current_env == Environment.PRODUCTION:
            config["pool_size"] = int(os.getenv("DB_POOL_SIZE", "50"))
            config["max_overflow"] = int(os.getenv("DB_MAX_OVERFLOW", "100"))
            config["echo"] = False
        elif self.current_env == Environment.TESTING:
            config["url"] = os.getenv("TEST_DATABASE_URL", "sqlite:///./test.db")
            config["pool_size"] = 5
            config["max_overflow"] = 10

        return config

    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration for current environment"""
        return {
            "debug": self.config.debug,
            "enable_docs": self.config.enable_docs
            and self.current_env != Environment.PRODUCTION,
            "cors_strict": self.current_env == Environment.PRODUCTION,
            "rate_limiting_enabled": self.current_env != Environment.TESTING,
            "ssl_required": self.current_env
            in [Environment.STAGING, Environment.PRODUCTION],
        }

    def get_feature_flags(self) -> Dict[str, bool]:
        """Get feature flags for current environment"""
        # @SPEC:FOUNDATION-001 @IMPL:0.1-feature-flags
        base_flags = {
            # Existing flags (8개)
            "enable_swagger_ui": self.current_env != Environment.PRODUCTION,
            "enable_redoc": self.current_env != Environment.PRODUCTION,
            "enable_metrics": True,
            "enable_rate_limiting": self.current_env != Environment.TESTING,
            "enable_request_logging": True,
            "enable_error_tracking": True,
            "enable_debug_toolbar": self.current_env == Environment.DEVELOPMENT,
            "enable_profiling": self.current_env
            in [Environment.DEVELOPMENT, Environment.STAGING],
            # PRD 1.5P flags (4개)
            "neural_case_selector": self._get_flag_override(
                "FEATURE_NEURAL_CASE_SELECTOR", False
            ),
            "soft_q_bandit": self._get_flag_override("FEATURE_SOFT_Q_BANDIT", False),
            "debate_mode": self._get_flag_override("FEATURE_DEBATE_MODE", False),
            "tools_policy": self._get_flag_override("FEATURE_TOOLS_POLICY", False),
            # Memento flags (3개)
            "meta_planner": self._get_flag_override("FEATURE_META_PLANNER", False),
            "mcp_tools": self._get_flag_override("FEATURE_MCP_TOOLS", False),
            "experience_replay": self._get_flag_override(
                "FEATURE_EXPERIENCE_REPLAY", False
            ),
        }
        return base_flags

    def _get_flag_override(self, env_var: str, default: bool) -> bool:
        """Get feature flag with environment variable override"""
        env_value = os.getenv(env_var, "").lower()
        if env_value in ("true", "1", "yes"):
            return True
        elif env_value in ("false", "0", "no"):
            return False
        return default

    def validate_environment(self) -> ValidationResult:
        """Validate current environment configuration"""
        validation_result: ValidationResult = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "recommendations": [],
        }

        # Check required environment variables
        required_vars = []
        if self.current_env == Environment.PRODUCTION:
            required_vars = ["SECRET_KEY", "DATABASE_URL"]
        elif self.current_env == Environment.STAGING:
            required_vars = ["SECRET_KEY", "DATABASE_URL"]

        for var in required_vars:
            if not os.getenv(var):
                validation_result["errors"].append(
                    f"Required environment variable {var} is not set"
                )
                validation_result["is_valid"] = False

        # Check database URL format
        db_url = os.getenv("DATABASE_URL", "")
        if db_url and not any(
            db_url.startswith(prefix) for prefix in ["sqlite:", "postgresql:", "mysql:"]
        ):
            validation_result["warnings"].append("DATABASE_URL format may be invalid")

        # Environment-specific recommendations
        if self.current_env == Environment.PRODUCTION:
            if os.getenv("DEBUG", "").lower() == "true":
                validation_result["warnings"].append(
                    "Debug mode is enabled in production"
                )

            if not os.getenv("REDIS_URL"):
                validation_result["recommendations"].append(
                    "Consider setting REDIS_URL for production caching"
                )

        if self.current_env == Environment.DEVELOPMENT:
            if not os.getenv("REDIS_URL"):
                validation_result["recommendations"].append(
                    "Set REDIS_URL for better development experience"
                )

        return validation_result

    def get_environment_summary(self) -> Dict[str, Any]:
        """Get summary of current environment"""
        return {
            "environment": self.current_env.value,
            "debug": self.config.debug,
            "testing": self.config.testing,
            "worker_processes": self.config.worker_processes,
            "log_level": self.config.log_level,
            "docs_enabled": self.config.enable_docs,
            "validation": self.validate_environment(),
        }


# Global instance
_env_manager = None


def get_env_manager() -> EnvironmentManager:
    """Get global environment manager instance"""
    global _env_manager
    if _env_manager is None:
        _env_manager = EnvironmentManager()
    return _env_manager


# Export main classes and functions
__all__ = ["Environment", "EnvironmentConfig", "EnvironmentManager", "get_env_manager"]
