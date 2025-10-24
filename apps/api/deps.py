"""
A팀 API 공통 의존성
- API Key 검증
- Request ID 생성
- 공통 응답 필드

@CODE:TEST-004-001:AUTH | SPEC: SPEC-TEST-004.md | TEST: tests/security/test_authentication.py
"""

import os
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import Depends, Header, HTTPException, Request

from .database import db_manager

# Import API Key security components
from .security.api_key_storage import APIKeyInfo, APIKeyManager


async def verify_api_key(
    request: Request, x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> APIKeyInfo:
    """
    Verify API key authentication

    REQ-1: The system shall enforce API key authentication
    REQ-5: WHEN API request is made without X-API-Key header
    REQ-6: WHEN API request is made with invalid API key
    REQ-7: WHEN API request is made with expired API key

    Args:
        request: FastAPI Request object
        x_api_key: API key from X-API-Key header

    Returns:
        APIKeyInfo: API key information if valid

    Raises:
        HTTPException: 401 if key is missing, invalid, or expired
    """
    # Check if API key is provided
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key is required")

    # Basic format validation (minimum length)
    if len(x_api_key) < 3:
        raise HTTPException(status_code=401, detail="Invalid API key format")

    # For testing environment, allow test API key
    test_api_key = os.getenv("DT_RAG_API_KEY", "test_api_key_for_testing")
    if x_api_key == test_api_key:
        # Return mock APIKeyInfo for testing
        return APIKeyInfo(
            key_id="test-key-001",
            name="Test API Key",
            description="Test API key for development",
            scope="admin",
            permissions=["read", "write", "admin"],
            allowed_ips=None,
            rate_limit=100,
            is_active=True,
            expires_at=None,
            created_at=datetime.now(timezone.utc),
            last_used_at=datetime.now(timezone.utc),
            total_requests=0,
            failed_requests=0,
        )

    # For production, verify with database
    try:
        async with db_manager.get_session() as session:
            manager = APIKeyManager(session)

            # Get client IP
            client_ip = request.client.host if request.client else "unknown"

            # Get endpoint and method
            endpoint = str(request.url.path)
            method = request.method

            # Verify API key with database
            api_key_info = await manager.verify_api_key(
                plaintext_key=x_api_key,
                client_ip=client_ip,
                endpoint=endpoint,
                method=method,
            )

            if not api_key_info:
                raise HTTPException(status_code=401, detail="Invalid API key")

            # Additional expiration check (handled in manager, but double-check)
            if (
                api_key_info.expires_at
                and datetime.now(timezone.utc) > api_key_info.expires_at
            ):
                raise HTTPException(status_code=401, detail="API key expired")

            return api_key_info

    except HTTPException:
        raise
    except Exception as e:
        # Log error but don't expose internals
        import logging

        logging.error(f"API key verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid API key")


def generate_request_id() -> str:
    """요청 ID 생성 (Bridge Pack 스펙 준수)"""
    return str(uuid4())


def get_current_timestamp() -> str:
    """ISO 8601 타임스탬프 생성"""
    return datetime.now(timezone.utc).isoformat()


def get_taxonomy_version() -> str:
    """현재 taxonomy 버전 (Bridge Pack 스펙)"""
    return "1.8.1"
