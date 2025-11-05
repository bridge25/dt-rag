"""
Langfuse LLM Cost Tracking Client for DT-RAG v1.8.1

Integrates Langfuse v3 SDK (OpenTelemetry-based) for comprehensive LLM cost monitoring:
- Gemini 2.5 Flash (RAGAS evaluation)
- OpenAI text-embedding-3-large (embedding generation)

Usage:
    from apps.api.monitoring.langfuse_client import observe, get_langfuse_client

    @observe(name="my_function", as_type="generation")
    async def my_llm_function():
        pass
"""

import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Lazy import to avoid startup errors
_langfuse_client: Optional[Any] = None
_langfuse_available = False

try:
    from langfuse import Langfuse
    from langfuse.decorators import observe

    _langfuse_available = True
except (ImportError, Exception) as e:
    # Catch all exceptions including Pydantic v1 type inference errors in Python 3.14+
    logger.warning(f"langfuse not available: {type(e).__name__}: {e}")

    # Fallback: no-op decorator
    def observe(name: str = "", as_type: str = "span", **kwargs: Any) -> Any:
        """No-op decorator when Langfuse is not available"""

        def decorator(func: Any) -> Any:
            return func

        return decorator


def get_langfuse_client() -> Optional[Any]:
    """
    Get singleton Langfuse client instance

    Returns:
        Langfuse client if available and enabled, None otherwise
    """
    global _langfuse_client

    if not _langfuse_available:
        return None

    if _langfuse_client is not None:
        return _langfuse_client

    # Initialize client
    enabled = os.getenv("LANGFUSE_ENABLED", "false").lower() == "true"

    if not enabled:
        logger.info("Langfuse is disabled (LANGFUSE_ENABLED=false)")
        return None

    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")

    if not public_key or not secret_key:
        logger.warning(
            "Langfuse credentials not found (LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY)"
        )
        return None

    try:
        _langfuse_client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
        )

        logger.info(f"Langfuse client initialized: {_langfuse_client.base_url}")
        return _langfuse_client

    except Exception as e:
        logger.error(f"Failed to initialize Langfuse client: {e}")
        return None


def get_langfuse_status() -> Dict[str, Any]:
    """
    Get Langfuse integration status

    Returns:
        Status dictionary with availability, configuration, and health info
    """
    status: Dict[str, Any] = {
        "available": _langfuse_available,
        "enabled": os.getenv("LANGFUSE_ENABLED", "false").lower() == "true",
        "configured": False,
        "client_initialized": _langfuse_client is not None,
    }

    if _langfuse_available:
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        status["configured"] = bool(public_key and secret_key)

    if _langfuse_client:
        try:
            # Test client health
            status["host"] = _langfuse_client._base_url
            status["health"] = "healthy"
        except Exception as e:
            status["health"] = f"unhealthy: {e}"

    return status


# Model cost configuration (USD per 1K tokens)
# Reference: https://ai.google.dev/pricing, https://openai.com/pricing
MODEL_COSTS = {
    "gemini-2.5-flash-latest": {
        "input_per_1k_tokens": 0.000075,  # $0.075 / 1M tokens
        "output_per_1k_tokens": 0.0003,  # $0.30 / 1M tokens
        "context_window": 128000,  # 128K tokens
    },
    "gemini-2.0-flash-exp": {
        "input_per_1k_tokens": 0.0,  # Free tier (experimental)
        "output_per_1k_tokens": 0.0,
        "context_window": 128000,
    },
    "text-embedding-3-large": {
        "input_per_1k_tokens": 0.00013,  # $0.13 / 1M tokens
        "output_per_1k_tokens": 0.0,  # Embeddings have no output
        "dimensions": 1536,
    },
    "text-embedding-ada-002": {
        "input_per_1k_tokens": 0.0001,  # $0.10 / 1M tokens
        "output_per_1k_tokens": 0.0,
        "dimensions": 1536,
    },
}


def calculate_cost(
    model: str, input_tokens: int, output_tokens: int = 0, exchange_rate: float = 1300.0
) -> Dict[str, float]:
    """
    Calculate LLM cost for a specific model

    Args:
        model: Model name (e.g., "gemini-2.5-flash-latest")
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens (default: 0 for embeddings)
        exchange_rate: USD to KRW exchange rate (default: 1300)

    Returns:
        Dictionary with cost_usd and cost_krw
    """
    if model not in MODEL_COSTS:
        logger.warning(f"Unknown model: {model}, cost calculation may be inaccurate")
        return {"cost_usd": 0.0, "cost_krw": 0.0}

    config = MODEL_COSTS[model]

    input_cost = (input_tokens / 1000) * config["input_per_1k_tokens"]
    output_cost = (output_tokens / 1000) * config["output_per_1k_tokens"]

    cost_usd = input_cost + output_cost
    cost_krw = cost_usd * exchange_rate

    return {
        "cost_usd": cost_usd,
        "cost_krw": cost_krw,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost_usd": input_cost,
        "output_cost_usd": output_cost,
    }


# Export main functions
__all__ = [
    "observe",
    "get_langfuse_client",
    "get_langfuse_status",
    "calculate_cost",
    "MODEL_COSTS",
]
