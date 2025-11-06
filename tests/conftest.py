"""
pytest configuration and shared fixtures for DT-RAG test suite

This file provides common test fixtures, configuration, and utilities
that can be used across all test modules in the DT-RAG system.
"""

import asyncio
import pytest
import os
import tempfile
import shutil
from pathlib import Path
from typing import AsyncGenerator, Generator, Dict, Any
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

# Test database and environment setup
os.environ["TESTING"] = "true"
# Use PostgreSQL with pgvector for vector similarity search
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/dt_rag_test"
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_database():
    """Mock database connection for unit tests."""
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock()
    mock_db.fetch = AsyncMock(return_value=[])
    mock_db.fetchrow = AsyncMock(return_value=None)
    mock_db.fetchval = AsyncMock(return_value=None)
    return mock_db


@pytest.fixture
def mock_redis():
    """Mock Redis connection for cache tests."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=1)
    mock_redis.exists = AsyncMock(return_value=False)
    return mock_redis


@pytest.fixture
def sample_document_data() -> Dict[str, Any]:
    """Sample document data for testing."""
    return {
        "id": "test-doc-1",
        "title": "Test Document",
        "content": "This is a test document for unit testing purposes.",
        "metadata": {
            "source": "test",
            "created_at": "2024-01-01T00:00:00Z",
            "tags": ["test", "document"],
        },
        "embeddings": [0.1, 0.2, 0.3, 0.4, 0.5],
    }


@pytest.fixture
def sample_search_query() -> Dict[str, Any]:
    """Sample search query for testing."""
    return {
        "query": "test search query",
        "filters": {"source": "test"},
        "limit": 10,
        "include_metadata": True,
    }


@pytest.fixture
def sample_api_key_data() -> Dict[str, Any]:
    """Sample API key data for testing."""
    return {
        "name": "test-api-key",
        "description": "Test API key for unit testing",
        "permissions": ["read", "write"],
    }


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for AI service tests."""
    mock_client = AsyncMock()
    mock_client.embeddings.create = AsyncMock()
    mock_client.chat.completions.create = AsyncMock()
    return mock_client


@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for external API calls."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock()
    mock_client.post = AsyncMock()
    mock_client.put = AsyncMock()
    mock_client.delete = AsyncMock()
    return mock_client


@pytest.fixture
async def api_client() -> AsyncGenerator:
    """
    Async HTTP client for integration tests

    Provides an httpx AsyncClient configured with the FastAPI app
    for testing async API endpoints without running a real server.
    """
    from httpx import AsyncClient, ASGITransport
    from apps.api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def sample_text() -> str:
    """Sample text for classification and search tests."""
    return "Machine learning is a subset of artificial intelligence that focuses on training algorithms."


class AsyncContextManager:
    """Helper class for async context manager mocking."""

    def __init__(self, return_value):
        self.return_value = return_value

    async def __aenter__(self):
        return self.return_value

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@pytest.fixture
def mock_async_session():
    """Mock SQLAlchemy async session for database tests."""
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    return AsyncContextManager(mock_session)


@pytest.fixture(scope="session", autouse=False)
async def setup_test_database():
    """Initialize test database with schema and golden dataset."""
    from tests.fixtures.test_db_schema import init_test_db, cleanup_test_db
    from apps.core.db_session import engine

    # Setup
    await init_test_db()
    yield

    # Teardown - ensure all connections are closed before cleanup
    # Wait for any pending operations to complete
    await asyncio.sleep(0.2)

    # Dispose engine connection pool first to close all active connections
    await engine.dispose()

    # Wait for connections to fully close
    await asyncio.sleep(0.3)

    # Now cleanup database
    await cleanup_test_db()


@pytest.fixture(scope="function")
async def setup_taxonomy_nodes():
    """테스트용 taxonomy_nodes 데이터 삽입"""
    from apps.api.database import TaxonomyNode
    from apps.core.db_session import async_session
    import uuid
    from sqlalchemy import text

    async with async_session() as session:
        await session.execute(
            text("DELETE FROM taxonomy_nodes WHERE version = '1.0.0'")
        )
        await session.commit()

    async with async_session() as session:
        test_nodes = [
            TaxonomyNode(
                node_id=uuid.uuid4(),
                label="technology",
                canonical_path=["technology"],
                version="1.0.0",
                confidence=1.0,
            ),
            TaxonomyNode(
                node_id=uuid.uuid4(),
                label="ai",
                canonical_path=["technology", "ai"],
                version="1.0.0",
                confidence=1.0,
            ),
            TaxonomyNode(
                node_id=uuid.uuid4(),
                label="machine-learning",
                canonical_path=["technology", "ai", "machine-learning"],
                version="1.0.0",
                confidence=1.0,
            ),
        ]

        for node in test_nodes:
            session.add(node)

        await session.commit()

    yield

    async with async_session() as session:
        await session.execute(
            text("DELETE FROM taxonomy_nodes WHERE version = '1.0.0'")
        )
        await session.commit()


@pytest.fixture(autouse=True)
async def cleanup_test_files():
    """Automatically cleanup test files after each test."""
    yield

    # Wait for DB connections to close
    await asyncio.sleep(0.1)

    # Retry cleanup with 3 attempts
    test_files = ["test.db", "test.log", "test_cache.json"]
    for file in test_files:
        for attempt in range(3):
            try:
                if os.path.exists(file):
                    os.remove(file)
                break
            except PermissionError:
                if attempt < 2:
                    await asyncio.sleep(0.05)
                else:
                    pass  # Skip if still locked


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "e2e: marks tests as end-to-end tests")
    config.addinivalue_line("markers", "slow: marks tests as slow running")


# Custom assertions and utilities
def assert_valid_uuid(value: str) -> bool:
    """Assert that a string is a valid UUID."""
    try:
        import uuid

        uuid.UUID(value)
        return True
    except ValueError:
        return False


def assert_valid_timestamp(value: str) -> bool:
    """Assert that a string is a valid ISO timestamp."""
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


# Export utilities for use in tests
__all__ = ["assert_valid_uuid", "assert_valid_timestamp", "AsyncContextManager"]
