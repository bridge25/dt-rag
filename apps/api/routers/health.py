"""
Health Check 엔드포인트
Bridge Pack ACCESS_CARD.md 스펙 100% 준수
"""

from fastapi import APIRouter, Depends
from deps import verify_api_key, get_current_timestamp, get_taxonomy_version

router = APIRouter()

@router.get("/healthz")
def health_check(api_key: str = Depends(verify_api_key)):
    """
    Bridge Pack 스펙: GET /healthz
    Expected Response:
    {
      "status": "healthy",
      "timestamp": "2025-09-05T14:45:00Z",
      "version": "1.8.1"
    }
    """
    return {
        "status": "healthy",
        "timestamp": get_current_timestamp(),
        "version": get_taxonomy_version(),
        "team": "A",
        "service": "taxonomy-api",
        "spec": "OpenAPI v1.8.1"
    }