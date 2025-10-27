"""
LLM Configuration Manager for DT-RAG v1.8.1

Manages configuration and initialization of Language Model services including
OpenAI, Anthropic, Azure OpenAI, and embedding services with fallback handling.
"""

import os
import logging
from typing import Dict, Any, Optional, List, TypedDict
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class ValidationResult(TypedDict):
    """Type definition for validation results"""

    is_valid: bool
    warnings: List[str]
    errors: List[str]
    recommendations: List[str]


class LLMProvider(Enum):
    """Supported LLM providers"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    DUMMY = "dummy"  # For testing/development without API keys


class EmbeddingProvider(Enum):
    """Supported embedding providers"""

    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    DUMMY = "dummy"  # For testing/development without API keys


@dataclass
class LLMServiceConfig:
    """Configuration for LLM service"""

    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    api_version: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7
    is_dummy: bool = False


@dataclass
class EmbeddingServiceConfig:
    """Configuration for embedding service"""

    provider: EmbeddingProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    api_version: Optional[str] = None
    dimensions: Optional[int] = None
    is_dummy: bool = False


class LLMConfigManager:
    """Manages LLM and embedding service configuration"""

    def __init__(self) -> None:
        self.llm_config = self._configure_llm_service()
        self.embedding_config = self._configure_embedding_service()

    def _configure_llm_service(self) -> LLMServiceConfig:
        """Configure primary LLM service with fallback"""

        # Try OpenAI first
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            return LLMServiceConfig(
                provider=LLMProvider.OPENAI,
                model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                api_key=openai_key,
                max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "1000")),
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
                is_dummy=False,
            )

        # Try Anthropic
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            return LLMServiceConfig(
                provider=LLMProvider.ANTHROPIC,
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
                api_key=anthropic_key,
                max_tokens=int(os.getenv("ANTHROPIC_MAX_TOKENS", "1000")),
                temperature=float(os.getenv("ANTHROPIC_TEMPERATURE", "0.7")),
                is_dummy=False,
            )

        # Try Azure OpenAI
        azure_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if azure_key and azure_endpoint:
            return LLMServiceConfig(
                provider=LLMProvider.AZURE_OPENAI,
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-35-turbo"),
                api_key=azure_key,
                base_url=azure_endpoint,
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2023-12-01-preview"),
                max_tokens=int(os.getenv("AZURE_OPENAI_MAX_TOKENS", "1000")),
                temperature=float(os.getenv("AZURE_OPENAI_TEMPERATURE", "0.7")),
                is_dummy=False,
            )

        # Fallback to dummy service
        logger.warning("No LLM API keys found, using dummy service")
        return LLMServiceConfig(
            provider=LLMProvider.DUMMY, model="dummy-model", is_dummy=True
        )

    def _configure_embedding_service(self) -> EmbeddingServiceConfig:
        """Configure embedding service with fallback"""

        # Try OpenAI embeddings first
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            return EmbeddingServiceConfig(
                provider=EmbeddingProvider.OPENAI,
                model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002"),
                api_key=openai_key,
                dimensions=int(os.getenv("OPENAI_EMBEDDING_DIMENSIONS", "1536")),
                is_dummy=False,
            )

        # Try Azure OpenAI embeddings
        azure_key = os.getenv("AZURE_OPENAI_API_KEY")
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if azure_key and azure_endpoint:
            return EmbeddingServiceConfig(
                provider=EmbeddingProvider.AZURE_OPENAI,
                model=os.getenv(
                    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002"
                ),
                api_key=azure_key,
                base_url=azure_endpoint,
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2023-12-01-preview"),
                dimensions=int(os.getenv("AZURE_OPENAI_EMBEDDING_DIMENSIONS", "1536")),
                is_dummy=False,
            )

        # Fallback to dummy service
        logger.warning("No embedding API keys found, using dummy service")
        return EmbeddingServiceConfig(
            provider=EmbeddingProvider.DUMMY,
            model="dummy-embedding",
            dimensions=1536,  # Standard dimension for compatibility
            is_dummy=True,
        )

    def get_llm_config(self) -> LLMServiceConfig:
        """Get LLM service configuration"""
        return self.llm_config

    def get_embedding_config(self) -> EmbeddingServiceConfig:
        """Get embedding service configuration"""
        return self.embedding_config

    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all configured services"""
        return {
            "llm_service": {
                "provider": self.llm_config.provider.value,
                "model": self.llm_config.model,
                "is_dummy": self.llm_config.is_dummy,
                "configured": not self.llm_config.is_dummy,
            },
            "embedding_service": {
                "provider": self.embedding_config.provider.value,
                "model": self.embedding_config.model,
                "is_dummy": self.embedding_config.is_dummy,
                "configured": not self.embedding_config.is_dummy,
            },
            "system_operational": not (
                self.llm_config.is_dummy and self.embedding_config.is_dummy
            ),
        }

    def validate_configuration(self) -> ValidationResult:
        """Validate current LLM configuration"""
        validation_result: ValidationResult = {
            "is_valid": True,
            "warnings": [],
            "errors": [],
            "recommendations": [],
        }

        # Check LLM service
        if self.llm_config.is_dummy:
            validation_result["warnings"].append("LLM service is using dummy provider")
            validation_result["recommendations"].append(
                "Configure OPENAI_API_KEY or ANTHROPIC_API_KEY for AI responses"
            )

        # Check embedding service
        if self.embedding_config.is_dummy:
            validation_result["warnings"].append(
                "Embedding service is using dummy provider"
            )
            validation_result["recommendations"].append(
                "Configure OPENAI_API_KEY for semantic search functionality"
            )

        # Check for API key security
        for key_name in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "AZURE_OPENAI_API_KEY"]:
            key_value = os.getenv(key_name)
            if key_value:
                if len(key_value) < 20:
                    validation_result["warnings"].append(
                        f"{key_name} appears to be too short"
                    )
                if key_value.startswith("sk-") and key_name != "OPENAI_API_KEY":
                    validation_result["warnings"].append(
                        f"{key_name} format may be incorrect"
                    )

        # Environment-specific recommendations
        environment = os.getenv("ENVIRONMENT", "development")
        if environment == "production":
            if self.llm_config.is_dummy or self.embedding_config.is_dummy:
                validation_result["errors"].append(
                    "Dummy services should not be used in production"
                )
                validation_result["is_valid"] = False

        return validation_result

    def get_available_models(self) -> Dict[str, List[str]]:
        """Get available models for each provider"""
        return {
            "openai": [
                "gpt-4",
                "gpt-4-turbo",
                "gpt-3.5-turbo",
                "text-embedding-ada-002",
                "text-embedding-3-small",
                "text-embedding-3-large",
            ],
            "anthropic": [
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307",
            ],
            "azure_openai": ["gpt-4", "gpt-35-turbo", "text-embedding-ada-002"],
        }

    def update_llm_config(self, config_updates: Dict[str, Any]) -> LLMServiceConfig:
        """Update LLM configuration (for runtime configuration changes)"""
        # Create new config with updates
        current_config = self.llm_config

        if "model" in config_updates:
            current_config.model = config_updates["model"]
        if "max_tokens" in config_updates:
            current_config.max_tokens = config_updates["max_tokens"]
        if "temperature" in config_updates:
            current_config.temperature = config_updates["temperature"]

        self.llm_config = current_config
        return current_config

    def update_embedding_config(
        self, config_updates: Dict[str, Any]
    ) -> EmbeddingServiceConfig:
        """Update embedding configuration (for runtime configuration changes)"""
        current_config = self.embedding_config

        if "model" in config_updates:
            current_config.model = config_updates["model"]
        if "dimensions" in config_updates:
            current_config.dimensions = config_updates["dimensions"]

        self.embedding_config = current_config
        return current_config


# Global instance
_llm_config_manager = None


def get_llm_config() -> LLMConfigManager:
    """Get global LLM configuration manager instance"""
    global _llm_config_manager
    if _llm_config_manager is None:
        _llm_config_manager = LLMConfigManager()
    return _llm_config_manager


# Export main classes and functions
__all__ = [
    "LLMProvider",
    "EmbeddingProvider",
    "LLMServiceConfig",
    "EmbeddingServiceConfig",
    "LLMConfigManager",
    "get_llm_config",
]
