"""
pytest configuration and fixtures for security tests

Provides test fixtures for security-related API tests including
authentication, authorization, input validation, and security checks.
"""

import pytest
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP client for testing FastAPI endpoints

    Provides an httpx AsyncClient configured with the FastAPI app
    for testing API endpoints without running a real server.
    """
    from apps.api.main import app

    # Create async client with ASGI transport
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client
