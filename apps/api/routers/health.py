"""Health check router"""

from fastapi import APIRouter
import time

router = APIRouter()


@router.get("/healthz")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy", "timestamp": time.time(), "service": "dt-rag-api"}
