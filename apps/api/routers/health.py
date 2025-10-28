"""Health check router"""

from typing import Dict, Any
from fastapi import APIRouter
import time

router = APIRouter()


# @CODE:MYPY-CONSOLIDATION-002 | Phase 3: no-untyped-def resolution
@router.get("/healthz")  # type: ignore[misc]
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return {"status": "healthy", "timestamp": time.time(), "service": "dt-rag-api"}
