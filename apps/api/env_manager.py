# @CODE:MYPY-001:PHASE2:BATCH5 | SPEC: .moai/specs/SPEC-MYPY-001/spec.md
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class Environment(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"
    STAGING = "staging"


@dataclass
class ConfigData:
    debug: bool = True
    testing: bool = False
    worker_processes: int = 1


class EnvManager:
    def __init__(self) -> None:
        self.current_env = self.get_environment()
        self.config = ConfigData(
            debug=self.get_bool("DEBUG", True),
            testing=self.get_bool("TESTING", False),
            worker_processes=self.get_int("WORKER_PROCESSES", 1),
        )

    def get(self, key: str, default: Any = None) -> Any:
        return os.environ.get(key, default)

    def get_str(self, key: str, default: str = "") -> str:
        return str(os.environ.get(key, default))

    def get_int(self, key: str, default: int = 0) -> int:
        try:
            return int(os.environ.get(key, default))
        except (ValueError, TypeError):
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        value = os.environ.get(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")

    def get_list(self, key: str, default: Optional[List[str]] = None) -> List[str]:
        if default is None:
            default = []
        value = os.environ.get(key, "")
        return (
            [item.strip() for item in value.split(",") if item.strip()]
            if value
            else default
        )

    def get_environment(self) -> Environment:
        env = self.get_str("ENVIRONMENT", "development").lower()
        try:
            return Environment(env)
        except ValueError:
            return Environment.DEVELOPMENT

    def get_database_config(self) -> Dict[str, Any]:
        return {
            "host": self.get_str("POSTGRES_HOST", "localhost"),
            "port": self.get_int("POSTGRES_PORT", 5432),
            "user": self.get_str("POSTGRES_USER", "postgres"),
            "password": self.get_str("POSTGRES_PASSWORD", "postgres"),
            "database": self.get_str("POSTGRES_DB", "postgres"),
            "url": self.get_str(
                "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres"
            ),
            "pool_size": self.get_int("DB_POOL_SIZE", 10),
            "max_overflow": self.get_int("DB_MAX_OVERFLOW", 20),
            "echo": self.get_bool("DB_ECHO", False),
        }

    def get_security_config(self) -> Dict[str, Any]:
        return {
            "api_key_header": self.get_str("API_KEY_HEADER", "X-API-Key"),
            "api_key_prefix": self.get_str("API_KEY_PREFIX", "dtrag_"),
            "cors_origins": self.get_list("CORS_ORIGINS", ["*"]),
            "cors_methods": self.get_list("CORS_METHODS", ["*"]),
            "cors_headers": self.get_list("CORS_HEADERS", ["*"]),
            "enable_docs": self.get_bool("ENABLE_DOCS", True),
        }

    def get_feature_flags(self) -> Dict[str, bool]:
        return {
            "enable_caching": self.get_bool("ENABLE_CACHING", True),
            "enable_monitoring": self.get_bool("ENABLE_MONITORING", True),
            "enable_rate_limiting": self.get_bool("ENABLE_RATE_LIMITING", False),
            "enable_authentication": self.get_bool("ENABLE_AUTHENTICATION", False),
            "enable_swagger_ui": self.get_bool("ENABLE_SWAGGER_UI", True),
            "enable_redoc": self.get_bool("ENABLE_REDOC", True),
            "enable_metrics": self.get_bool("ENABLE_METRICS", True),
            "enable_request_logging": self.get_bool("ENABLE_REQUEST_LOGGING", True),
            "enable_error_tracking": self.get_bool("ENABLE_ERROR_TRACKING", True),
        }


def get_env_manager() -> EnvManager:
    return EnvManager()
