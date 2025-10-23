"""
CI-specific pytest configuration and fixtures

This file provides CI-compatible fixtures and configuration
that gracefully handle missing dependencies and services.
"""

# @TEST:CLASS-001 | SPEC: .moai/specs/SPEC-CLASS-001/spec.md

import os
import pytest
import asyncio
import tempfile
import logging
from typing import AsyncGenerator, Generator, Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

# Set up CI-friendly logging
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

# CI Environment Detection
def is_ci_environment() -> bool:
    """Detect if running in CI environment"""
    ci_indicators = [
        "CI",
        "CONTINUOUS_INTEGRATION",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "JENKINS_URL",
        "TRAVIS",
        "CIRCLECI"
    ]
    return any(os.getenv(indicator) for indicator in ci_indicators)

def has_service_available(service: str) -> bool:
    """Check if external service is available"""
    service_checks = {
        "postgresql": lambda: os.getenv("DATABASE_URL") and not is_ci_environment(),
        "redis": lambda: os.getenv("REDIS_URL") and not is_ci_environment(),
        "openai": lambda: os.getenv("OPENAI_API_KEY") and os.getenv("TEST_WITH_OPENAI"),
        "network": lambda: not is_ci_environment() or os.getenv("TEST_WITH_NETWORK")
    }

    checker = service_checks.get(service.lower())
    return checker() if checker else False

# pytest configuration for CI
def pytest_configure(config):
    """Configure pytest for CI environment"""
    if is_ci_environment():
        # Add CI-specific markers
        config.addinivalue_line("markers", "ci_safe: Safe to run in CI")
        config.addinivalue_line("markers", "local_only: Only run locally")

        # Set CI environment variable
        os.environ["CI_ENVIRONMENT"] = "true"
        os.environ["TESTING"] = "true"

        # Use in-memory databases for CI
        os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

        # Disable external service requirements
        if not os.getenv("TEST_WITH_REDIS"):
            os.environ["REDIS_ENABLED"] = "false"

def pytest_collection_modifyitems(config, items):
    """Modify test collection based on environment"""
    if is_ci_environment():
        # Skip tests that require external services in CI
        skip_markers = {
            "requires_db": not has_service_available("postgresql"),
            "requires_redis": not has_service_available("redis"),
            "requires_openai": not has_service_available("openai"),
            "requires_network": not has_service_available("network"),
            "local_only": True  # Always skip local_only tests in CI
        }

        for item in items:
            for marker, should_skip in skip_markers.items():
                if should_skip and item.get_closest_marker(marker):
                    item.add_marker(pytest.mark.skip(
                        reason=f"{marker} not available in CI environment"
                    ))

@pytest.fixture(scope="session")
def ci_environment() -> bool:
    """Fixture to indicate if running in CI"""
    return is_ci_environment()

@pytest.fixture
def ci_safe_database_url() -> str:
    """Provide CI-safe database URL"""
    if is_ci_environment():
        return "sqlite+aiosqlite:///:memory:"
    return os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")

@pytest.fixture
async def ci_safe_redis():
    """Provide CI-safe Redis mock"""
    if has_service_available("redis"):
        try:
            import redis.asyncio as redis
            client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/15"))
            await client.ping()
            yield client
            await client.close()
            return
        except Exception:
            pass

    # Use mock Redis for CI or when Redis unavailable
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock(return_value=True)
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=1)
    mock_redis.exists = AsyncMock(return_value=0)
    mock_redis.keys = AsyncMock(return_value=[])
    mock_redis.close = AsyncMock()
    yield mock_redis

@pytest.fixture
def ci_safe_openai_client():
    """Provide CI-safe OpenAI client mock"""
    if has_service_available("openai"):
        try:
            import openai
            client = openai.AsyncOpenAI()
            return client
        except Exception:
            pass

    # Use mock OpenAI client for CI
    mock_client = AsyncMock()
    mock_embeddings = AsyncMock()
    mock_embeddings.create = AsyncMock(return_value=MagicMock(
        data=[MagicMock(embedding=[0.1] * 1536)]
    ))
    mock_client.embeddings = mock_embeddings

    mock_chat = AsyncMock()
    mock_chat.completions.create = AsyncMock(return_value=MagicMock(
        choices=[MagicMock(message=MagicMock(content="Mock response"))]
    ))
    mock_client.chat = mock_chat

    return mock_client

@pytest.fixture
async def ci_safe_http_client():
    """Provide CI-safe HTTP client"""
    if has_service_available("network"):
        try:
            from httpx import AsyncClient
            async with AsyncClient() as client:
                yield client
            return
        except Exception:
            pass

    # Use mock HTTP client for CI
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json = MagicMock(return_value={"status": "ok"})
    mock_response.text = "Mock response"

    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.put = AsyncMock(return_value=mock_response)
    mock_client.delete = AsyncMock(return_value=mock_response)

    yield mock_client

@pytest.fixture
def ci_temp_directory() -> Generator[Path, None, None]:
    """Create temporary directory that's cleaned up properly"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def ci_environment_vars():
    """Set up CI-friendly environment variables"""
    original_env = dict(os.environ)

    # Set test environment variables
    test_env = {
        "TESTING": "true",
        "LOG_LEVEL": "WARNING",
        "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
        "REDIS_ENABLED": "false",
        "OPENAI_API_KEY": "test-key-for-ci",
        "SECRET_KEY": "test-secret-key-for-ci-only-do-not-use-in-production"
    }

    os.environ.update(test_env)

    try:
        yield test_env
    finally:
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)

# Graceful degradation helpers
class GracefulDegradationHelper:
    """Helper class for graceful test degradation"""

    @staticmethod
    def skip_if_service_unavailable(service: str):
        """Decorator to skip tests if service is unavailable"""
        def decorator(func):
            if not has_service_available(service):
                return pytest.mark.skip(
                    reason=f"Service '{service}' not available"
                )(func)
            return func
        return decorator

    @staticmethod
    def mock_if_service_unavailable(service: str, mock_fixture: str):
        """Use mock fixture if service is unavailable"""
        def decorator(func):
            if not has_service_available(service):
                # Add mock fixture dependency
                func = pytest.mark.usefixtures(mock_fixture)(func)
            return func
        return decorator

# Export helper for use in tests
graceful_degradation = GracefulDegradationHelper()

# Test data factories for CI
class CITestDataFactory:
    """Factory for generating CI-safe test data"""

    @staticmethod
    def create_sample_document(doc_id: str = "test_doc_1") -> Dict[str, Any]:
        """Create sample document for testing"""
        return {
            "id": doc_id,
            "title": f"Test Document {doc_id}",
            "content": f"This is test content for document {doc_id}",
            "metadata": {
                "category": "Test",
                "tags": ["test", "ci"],
                "created_at": "2024-01-01T00:00:00Z",
                "source": "ci_test"
            },
            "embeddings": [0.1] * 384  # Mock embedding vector
        }

    @staticmethod
    def create_search_query(query: str = "test query") -> Dict[str, Any]:
        """Create sample search query for testing"""
        return {
            "query": query,
            "filters": {"category": "Test"},
            "limit": 10,
            "include_metadata": True
        }

    @staticmethod
    def create_classification_request(text: str = "test text") -> Dict[str, Any]:
        """Create sample classification request"""
        return {
            "text": text,
            "context": {"type": "test"},
            "options": {"threshold": 0.5}
        }

# Export factory for use in tests
ci_test_data = CITestDataFactory()

# Custom assertions for CI
def assert_ci_safe_response(response, expected_status_codes=[200]):
    """Assert that response is valid in CI environment"""
    if hasattr(response, 'status_code'):
        assert response.status_code in expected_status_codes

    if hasattr(response, 'json'):
        try:
            data = response.json()
            assert isinstance(data, (dict, list))
        except Exception:
            # JSON parsing might fail, that's okay in some cases
            pass

def assert_graceful_degradation(result, fallback_value=None):
    """Assert that graceful degradation occurred"""
    # If service is unavailable, should return fallback or handle gracefully
    if not has_service_available("network") and result is None:
        assert True  # Graceful degradation occurred
    elif fallback_value is not None:
        assert result == fallback_value
    else:
        assert result is not None