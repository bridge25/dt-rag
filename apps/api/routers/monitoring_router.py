"""Monitoring router with Langfuse LLM cost tracking"""

from typing import Any, Dict
from fastapi import APIRouter
import time
import psutil
import os
from datetime import datetime

# Import API key authentication
try:
    from ..deps import verify_api_key
    from ..security import api_key_storage  # noqa: F401

    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False

    # @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
    def verify_api_key() -> None:
        return None


# Import Langfuse client
try:
    from ..monitoring.langfuse_client import (
        get_langfuse_client,
        get_langfuse_status,
        calculate_cost,
        MODEL_COSTS,
    )

    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
@router.get("/health")  # type: ignore[misc]
async def get_system_health() -> Dict[str, Any]:
    """Get comprehensive system health status"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return {
            "status": "healthy",
            "timestamp": time.time(),
            "system_info": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2),
            },
            "services": {
                "api": "running",
                "database": "fallback_mode",
                "cache": "memory_only",
            },
        }
    except Exception as e:
        return {
            "status": "partial",
            "timestamp": time.time(),
            "system_info": "limited",
            "services": {
                "api": "running",
                "database": "fallback_mode",
                "cache": "memory_only",
            },
            "error": str(e),
        }


# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
@router.get("/llm-costs")  # type: ignore[misc]
async def get_llm_costs() -> Dict[str, Any]:
    """
    Get LLM cost tracking dashboard (Gemini 2.5 Flash + OpenAI Embedding)

    Returns:
        - Total cost (USD, KRW)
        - Cost breakdown by model
        - Average cost per query
        - Target budget compliance (₩10/query)
        - Pricing information
    """
    if not LANGFUSE_AVAILABLE:
        return {
            "status": "unavailable",
            "message": "Langfuse integration not available. Install: pip install langfuse>=3.6.0",
            "setup_instructions": {
                "1": "Install langfuse: pip install langfuse>=3.6.0",
                "2": "Set LANGFUSE_PUBLIC_KEY in .env.local",
                "3": "Set LANGFUSE_SECRET_KEY in .env.local",
                "4": "Set LANGFUSE_ENABLED=true in .env.local",
            },
        }

    # Check Langfuse status
    langfuse_status = get_langfuse_status()
    if not langfuse_status.get("enabled"):
        return {
            "status": "disabled",
            "message": "Langfuse is disabled. Set LANGFUSE_ENABLED=true",
            "langfuse_status": langfuse_status,
        }

    if not langfuse_status.get("configured"):
        return {
            "status": "not_configured",
            "message": "Langfuse credentials not configured",
            "langfuse_status": langfuse_status,
        }

    try:
        client = get_langfuse_client()
        if not client:
            raise Exception("Langfuse client initialization failed")

        # Get traces from Langfuse (last 1000)
        # Note: Actual implementation depends on Langfuse SDK API
        # This is a placeholder for the structure

        # Simulated data structure (replace with actual client.get_traces())
        traces: list[Any] = []  # client.get_traces(limit=1000)

        # Calculate costs by model
        gemini_cost_usd = 0.0
        embedding_cost_usd = 0.0
        total_queries = len(traces) if traces else 0

        # Exchange rate
        exchange_rate = float(os.getenv("USD_TO_KRW", "1300"))

        # Cost breakdown
        for trace in traces:
            model_name = getattr(trace, "model", "unknown").lower()
            input_tokens = getattr(trace, "input_tokens", 0)
            output_tokens = getattr(trace, "output_tokens", 0)

            if "gemini" in model_name:
                cost_info = calculate_cost(
                    "gemini-2.5-flash-latest", input_tokens, output_tokens
                )
                gemini_cost_usd += cost_info["cost_usd"]
            elif "embedding" in model_name:
                cost_info = calculate_cost("text-embedding-3-large", input_tokens, 0)
                embedding_cost_usd += cost_info["cost_usd"]

        total_cost_usd = gemini_cost_usd + embedding_cost_usd
        avg_cost_per_query_usd = (
            (total_cost_usd / total_queries) if total_queries > 0 else 0
        )
        avg_cost_per_query_krw = avg_cost_per_query_usd * exchange_rate

        # Target budget (₩10/query)
        target_cost_krw = 10.0
        is_within_budget = avg_cost_per_query_krw <= target_cost_krw

        return {
            "status": "active",
            "timestamp": datetime.now().isoformat(),
            "total_queries": total_queries,
            "costs": {
                "total_usd": round(total_cost_usd, 4),
                "total_krw": round(total_cost_usd * exchange_rate, 2),
                "breakdown_krw": {
                    "gemini_2.5_flash": round(gemini_cost_usd * exchange_rate, 2),
                    "openai_embedding_3_large": round(
                        embedding_cost_usd * exchange_rate, 2
                    ),
                },
            },
            "per_query": {
                "avg_cost_usd": round(avg_cost_per_query_usd, 6),
                "avg_cost_krw": round(avg_cost_per_query_krw, 2),
                "target_krw": target_cost_krw,
                "is_within_budget": is_within_budget,
                "budget_utilization_percent": (
                    round((avg_cost_per_query_krw / target_cost_krw) * 100, 2)
                    if target_cost_krw > 0
                    else 0
                ),
            },
            "pricing_info": MODEL_COSTS,
            "exchange_rate": exchange_rate,
            "langfuse_status": langfuse_status,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "langfuse_status": langfuse_status if "langfuse_status" in locals() else {},
        }


# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
@router.get("/langfuse-status")  # type: ignore[misc]
async def get_langfuse_integration_status() -> Dict[str, Any]:
    """Get Langfuse integration status and configuration"""
    if not LANGFUSE_AVAILABLE:
        return {"available": False, "message": "Langfuse package not installed"}

    status = get_langfuse_status()
    return status
