"""
LLM and AI Services Configuration Management
Provides secure, fallback-enabled configuration for LLM and embedding services.
"""

import os
import logging
from typing import Optional, Dict, Any, Literal
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ServiceMode(str, Enum):
    """Available service modes for LLM and embedding services"""
    DUMMY = "dummy"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"

@dataclass
class LLMServiceConfig:
    """Configuration for LLM services with fallback support"""
    mode: ServiceMode = ServiceMode.DUMMY

    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_org_id: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"

    # Anthropic Configuration
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-sonnet-20240229"

    # Azure OpenAI Configuration
    azure_api_key: Optional[str] = None
    azure_endpoint: Optional[str] = None
    azure_api_version: str = "2024-02-15-preview"
    azure_deployment_name: str = "gpt-35-turbo"

    # Fallback/Dummy Configuration
    dummy_response_delay: float = 0.1
    enable_dummy_responses: bool = True

    # General Settings
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 30
    max_retries: int = 3

@dataclass
class EmbeddingServiceConfig:
    """Configuration for embedding services with fallback support"""
    mode: ServiceMode = ServiceMode.DUMMY

    # OpenAI Embeddings
    openai_api_key: Optional[str] = None
    openai_model: str = "text-embedding-3-small"

    # Azure OpenAI Embeddings
    azure_api_key: Optional[str] = None
    azure_endpoint: Optional[str] = None
    azure_api_version: str = "2024-02-15-preview"
    azure_deployment_name: str = "text-embedding-3-small"

    # Embedding Configuration
    dimensions: int = 1536
    batch_size: int = 100

    # Fallback/Dummy Configuration
    dummy_dimensions: int = 1536
    enable_random_embeddings: bool = True

    # Performance Settings
    timeout: int = 30
    max_retries: int = 3

class LLMConfigManager:
    """
    Manages LLM and embedding service configurations with secure fallback mechanisms
    """

    def __init__(self):
        self.llm_config = self._load_llm_config()
        self.embedding_config = self._load_embedding_config()

    def _load_llm_config(self) -> LLMServiceConfig:
        """Load LLM configuration from environment variables"""
        config = LLMServiceConfig()

        # Determine service mode
        mode = os.getenv("LLM_SERVICE_MODE", "dummy").lower()
        try:
            config.mode = ServiceMode(mode)
        except ValueError:
            logger.warning(f"Invalid LLM_SERVICE_MODE: {mode}, falling back to dummy")
            config.mode = ServiceMode.DUMMY

        # OpenAI Configuration
        config.openai_api_key = os.getenv("OPENAI_API_KEY")
        config.openai_org_id = os.getenv("OPENAI_ORG_ID")
        config.openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

        # Anthropic Configuration
        config.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        config.anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229")

        # Azure Configuration
        config.azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        config.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        config.azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        config.azure_deployment_name = os.getenv("AZURE_DEPLOYMENT_NAME", "gpt-35-turbo")

        # Fallback Configuration
        config.dummy_response_delay = float(os.getenv("DUMMY_LLM_RESPONSE_DELAY", "0.1"))
        config.enable_dummy_responses = os.getenv("ENABLE_DUMMY_RESPONSES", "true").lower() == "true"

        # General Settings
        config.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "4096"))
        config.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        config.timeout = int(os.getenv("LLM_TIMEOUT", "30"))
        config.max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))

        return config

    def _load_embedding_config(self) -> EmbeddingServiceConfig:
        """Load embedding configuration from environment variables"""
        config = EmbeddingServiceConfig()

        # Determine service mode
        mode = os.getenv("EMBEDDING_SERVICE_MODE", "dummy").lower()
        try:
            config.mode = ServiceMode(mode)
        except ValueError:
            logger.warning(f"Invalid EMBEDDING_SERVICE_MODE: {mode}, falling back to dummy")
            config.mode = ServiceMode.DUMMY

        # OpenAI Configuration
        config.openai_api_key = os.getenv("OPENAI_API_KEY")
        config.openai_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

        # Azure Configuration
        config.azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        config.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        config.azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        config.azure_deployment_name = os.getenv("AZURE_EMBEDDING_DEPLOYMENT_NAME", "text-embedding-3-small")

        # Embedding Configuration
        config.dimensions = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))
        config.batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "100"))

        # Fallback Configuration
        config.dummy_dimensions = int(os.getenv("DUMMY_EMBEDDING_DIMENSIONS", "1536"))
        config.enable_random_embeddings = os.getenv("ENABLE_DUMMY_RESPONSES", "true").lower() == "true"

        # Performance Settings
        config.timeout = int(os.getenv("EMBEDDING_TIMEOUT", "30"))
        config.max_retries = int(os.getenv("EMBEDDING_MAX_RETRIES", "3"))

        return config

    def validate_llm_config(self) -> Dict[str, Any]:
        """
        Validate LLM configuration and return status

        Returns:
            Dict containing validation results and service status
        """
        result = {
            "mode": self.llm_config.mode.value,
            "is_valid": False,
            "has_api_key": False,
            "fallback_available": True,
            "warnings": [],
            "errors": []
        }

        if self.llm_config.mode == ServiceMode.DUMMY:
            result["is_valid"] = True
            result["warnings"].append("Using dummy LLM mode - no real API calls will be made")

        elif self.llm_config.mode == ServiceMode.OPENAI:
            if self.llm_config.openai_api_key:
                result["has_api_key"] = True
                result["is_valid"] = True
            else:
                result["errors"].append("OpenAI API key not configured")
                result["warnings"].append("Falling back to dummy mode")

        elif self.llm_config.mode == ServiceMode.ANTHROPIC:
            if self.llm_config.anthropic_api_key:
                result["has_api_key"] = True
                result["is_valid"] = True
            else:
                result["errors"].append("Anthropic API key not configured")
                result["warnings"].append("Falling back to dummy mode")

        elif self.llm_config.mode == ServiceMode.AZURE:
            if self.llm_config.azure_api_key and self.llm_config.azure_endpoint:
                result["has_api_key"] = True
                result["is_valid"] = True
            else:
                missing = []
                if not self.llm_config.azure_api_key:
                    missing.append("AZURE_OPENAI_API_KEY")
                if not self.llm_config.azure_endpoint:
                    missing.append("AZURE_OPENAI_ENDPOINT")
                result["errors"].append(f"Azure configuration missing: {', '.join(missing)}")
                result["warnings"].append("Falling back to dummy mode")

        return result

    def validate_embedding_config(self) -> Dict[str, Any]:
        """
        Validate embedding configuration and return status

        Returns:
            Dict containing validation results and service status
        """
        result = {
            "mode": self.embedding_config.mode.value,
            "is_valid": False,
            "has_api_key": False,
            "fallback_available": True,
            "warnings": [],
            "errors": []
        }

        if self.embedding_config.mode == ServiceMode.DUMMY:
            result["is_valid"] = True
            result["warnings"].append("Using dummy embedding mode - random vectors will be generated")

        elif self.embedding_config.mode == ServiceMode.OPENAI:
            if self.embedding_config.openai_api_key:
                result["has_api_key"] = True
                result["is_valid"] = True
            else:
                result["errors"].append("OpenAI API key not configured for embeddings")
                result["warnings"].append("Falling back to dummy mode")

        elif self.embedding_config.mode == ServiceMode.AZURE:
            if self.embedding_config.azure_api_key and self.embedding_config.azure_endpoint:
                result["has_api_key"] = True
                result["is_valid"] = True
            else:
                missing = []
                if not self.embedding_config.azure_api_key:
                    missing.append("AZURE_OPENAI_API_KEY")
                if not self.embedding_config.azure_endpoint:
                    missing.append("AZURE_OPENAI_ENDPOINT")
                result["errors"].append(f"Azure embedding configuration missing: {', '.join(missing)}")
                result["warnings"].append("Falling back to dummy mode")

        return result

    def get_effective_llm_mode(self) -> ServiceMode:
        """
        Get the effective LLM mode after validation
        Falls back to dummy if configured mode is invalid
        """
        validation = self.validate_llm_config()
        if validation["is_valid"] and validation.get("has_api_key", True):
            return self.llm_config.mode
        else:
            return ServiceMode.DUMMY

    def get_effective_embedding_mode(self) -> ServiceMode:
        """
        Get the effective embedding mode after validation
        Falls back to dummy if configured mode is invalid
        """
        validation = self.validate_embedding_config()
        if validation["is_valid"] and validation.get("has_api_key", True):
            return self.embedding_config.mode
        else:
            return ServiceMode.DUMMY

    def should_use_dummy_llm(self) -> bool:
        """Check if dummy LLM mode should be used"""
        return self.get_effective_llm_mode() == ServiceMode.DUMMY

    def should_use_dummy_embeddings(self) -> bool:
        """Check if dummy embedding mode should be used"""
        return self.get_effective_embedding_mode() == ServiceMode.DUMMY

    def get_service_status(self) -> Dict[str, Any]:
        """
        Get comprehensive service status for monitoring

        Returns:
            Dict containing complete service configuration status
        """
        llm_validation = self.validate_llm_config()
        embedding_validation = self.validate_embedding_config()

        return {
            "llm_service": {
                "configured_mode": self.llm_config.mode.value,
                "effective_mode": self.get_effective_llm_mode().value,
                "is_dummy": self.should_use_dummy_llm(),
                "validation": llm_validation
            },
            "embedding_service": {
                "configured_mode": self.embedding_config.mode.value,
                "effective_mode": self.get_effective_embedding_mode().value,
                "is_dummy": self.should_use_dummy_embeddings(),
                "validation": embedding_validation
            },
            "fallback_available": True,
            "system_operational": True  # Always true due to fallback mechanisms
        }

# Global instance
_llm_config_manager: Optional[LLMConfigManager] = None

def get_llm_config() -> LLMConfigManager:
    """Get global LLM configuration manager instance"""
    global _llm_config_manager
    if _llm_config_manager is None:
        _llm_config_manager = LLMConfigManager()
    return _llm_config_manager

def get_llm_service_config() -> LLMServiceConfig:
    """Get LLM service configuration"""
    return get_llm_config().llm_config

def get_embedding_service_config() -> EmbeddingServiceConfig:
    """Get embedding service configuration"""
    return get_llm_config().embedding_config

# Convenience functions for service status
def is_llm_service_available() -> bool:
    """Check if LLM service is available (including dummy)"""
    return True  # Always true due to dummy fallback

def is_embedding_service_available() -> bool:
    """Check if embedding service is available (including dummy)"""
    return True  # Always true due to dummy fallback

def get_api_key_status() -> Dict[str, bool]:
    """Get status of all configured API keys"""
    config = get_llm_config()
    return {
        "openai": bool(config.llm_config.openai_api_key),
        "anthropic": bool(config.llm_config.anthropic_api_key),
        "azure": bool(config.llm_config.azure_api_key and config.llm_config.azure_endpoint)
    }

__all__ = [
    "ServiceMode",
    "LLMServiceConfig",
    "EmbeddingServiceConfig",
    "LLMConfigManager",
    "get_llm_config",
    "get_llm_service_config",
    "get_embedding_service_config",
    "is_llm_service_available",
    "is_embedding_service_available",
    "get_api_key_status"
]