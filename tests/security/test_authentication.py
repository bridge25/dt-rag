"""
API Key Authentication Tests

Tests for API key authentication security:
- Missing API key rejection
- Invalid API key rejection
- Expired API key rejection
- Health check endpoint exemption

@TEST:SECURITY-001
"""

import pytest
from httpx import AsyncClient


# @TEST:TEST-004
@pytest.mark.asyncio
async def test_api_requires_authentication(async_client: AsyncClient) -> None:
    """
    모든 API 엔드포인트는 인증 필요
    REQ-1, REQ-5
    """
    # Test endpoints that should require authentication
    endpoints = [
        ("/reflection/analyze", "POST", {"case_id": "test-001"}),
        ("/reflection/batch", "POST", {"case_ids": ["test-001"]}),
        ("/consolidation/run", "POST", {}),
    ]

    for path, method, payload in endpoints:
        if method == "POST":
            response = await async_client.post(path, json=payload)
        elif method == "GET":
            response = await async_client.get(path)

        # Should return 401 or 403 (not authenticated)
        assert response.status_code in [
            401,
            403,
        ], f"{path} should require authentication, got {response.status_code}"

        detail = response.json().get("detail", "")
        assert (
            "API key" in detail or "api key" in detail.lower()
        ), f"Error message should mention API key, got: {detail}"


# @TEST:TEST-004
@pytest.mark.asyncio
async def test_invalid_api_key_rejected(async_client: AsyncClient) -> None:
    """
    유효하지 않은 API 키는 거부됨
    REQ-6
    """
    response = await async_client.post(
        "/reflection/analyze",
        json={"case_id": "test-001"},
        headers={"X-API-Key": "invalid_api_key_12345"},
    )

    # Should return 401 or 403
    assert response.status_code in [
        401,
        403,
    ], f"Invalid API key should be rejected, got {response.status_code}"

    detail = response.json().get("detail", "")
    assert (
        "Invalid" in detail or "invalid" in detail.lower()
    ), f"Error message should mention invalid key, got: {detail}"


# @TEST:TEST-004
@pytest.mark.asyncio
async def test_expired_api_key_rejected(async_client: AsyncClient) -> None:
    """
    만료된 API 키는 거부됨
    REQ-7

    Note: This test requires implementation of API key expiration logic
    """
    # TODO: Implement API key expiration in deps.py
    # For now, test with a specifically formatted expired key
    response = await async_client.post(
        "/reflection/analyze",
        json={"case_id": "test-001"},
        headers={"X-API-Key": "expired_api_key_12345"},
    )

    # Should return 401 or 403
    assert response.status_code in [
        401,
        403,
    ], f"Expired API key should be rejected, got {response.status_code}"


# @TEST:TEST-004
@pytest.mark.asyncio
async def test_health_check_no_auth_required(async_client: AsyncClient) -> None:
    """
    Health check 엔드포인트는 인증 불필요
    REQ-1 (exception case)
    """
    # Health check should work without authentication
    response = await async_client.get("/health")

    # Should succeed (200 or 204) or return 404 if endpoint doesn't exist yet
    assert response.status_code in [
        200,
        204,
        404,
    ], f"Health check should not require auth or return 404, got {response.status_code}"

    # If endpoint exists, it should not ask for authentication
    if response.status_code != 404:
        # Should not contain authentication error
        if response.status_code >= 400:
            detail = response.json().get("detail", "")
            assert (
                "API key" not in detail.lower()
            ), f"Health check should not require API key, but got: {detail}"


# @TEST:TEST-004
@pytest.mark.asyncio
async def test_valid_api_key_accepted(async_client: AsyncClient) -> None:
    """
    유효한 API 키는 허용됨
    REQ-1 (success case)
    """
    import os

    valid_api_key = os.getenv("DT_RAG_API_KEY", "test_api_key_for_testing")

    response = await async_client.post(
        "/reflection/analyze",
        json={"case_id": "test-001"},
        headers={"X-API-Key": valid_api_key},
    )

    # Should NOT return 401/403 (authentication should pass)
    # May return 404 (case not found) or 422 (validation error) which is OK
    assert response.status_code not in [
        401,
        403,
    ], f"Valid API key should be accepted, got {response.status_code}: {response.json()}"
