"""
Pytest configuration and fixtures for dt-rag tests
@CODE:IMPORT-ASYNC-FIX-001 | SPEC: SPEC-IMPORT-ASYNC-FIX-001.md
"""
import pytest
import os
import sys
from typing import Generator
import asyncio
import subprocess

# Add apps/api to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'apps', 'api'))

# Set test environment
os.environ['DATABASE_URL'] = os.getenv(
    'TEST_DATABASE_URL',
    'postgresql+asyncpg://postgres:postgres@localhost:5432/dt_rag_test'
)
os.environ['NODE_ENV'] = 'test'
os.environ['DT_RAG_API_KEY'] = os.getenv('DT_RAG_API_KEY', 'test_api_key_for_testing')


# @pytest.fixture(scope="session")
# def event_loop() -> Generator:
#     """Create event loop for async tests"""
#     # Removed: Let pytest-asyncio handle event loop management automatically
#     loop = asyncio.get_event_loop_policy().new_event_loop()
#     yield loop
#     loop.close()


@pytest.fixture(scope="function")
async def db_engine():
    """Database engine fixture (function-scoped for proper event loop management)"""
    from database import engine
    yield engine
    # Don't dispose - let the global engine handle its own lifecycle


@pytest.fixture(scope="function")
async def db_session(db_engine):
    """Database session fixture with rollback (ensures test isolation)"""
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.ext.asyncio import async_sessionmaker

    async_session = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        transaction = await session.begin()
        yield session
        await transaction.rollback()  # Always rollback to ensure test isolation


@pytest.fixture(scope="module")
def api_client():
    """FastAPI test client"""
    from fastapi.testclient import TestClient
    from apps.api.main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
def sample_text() -> str:
    """Sample text for classification testing"""
    return "Retrieval-Augmented Generation (RAG) is a technique that combines information retrieval with language generation to produce more accurate and contextual responses."


@pytest.fixture(scope="function")
def ml_model_name() -> str:
    """ML model name for testing"""
    return os.getenv('ML_MODEL_NAME', 'all-MiniLM-L6-v2')


@pytest.fixture
async def sample_case_bank(db_session):
    """
    Create sample case_bank data for Reflection/Consolidation tests
    @CODE:TEST-002:FIXTURE | SPEC: SPEC-TEST-002.md
    """
    try:
        from apps.api.database import CaseBank
        from sqlalchemy import delete

        # Ensure table exists
        from apps.api.database import Base, engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Delete existing test cases first (for test isolation)
        await db_session.execute(
            delete(CaseBank).where(
                CaseBank.case_id.in_([
                    "test-case-001", "test-case-002", "test-case-003",
                    "test-case-004", "test-case-005"
                ])
            )
        )
        await db_session.flush()

        # Create 5 test cases with varying success rates
        test_cases = [
            CaseBank(
                case_id="test-case-001",
                query="How to implement RAG system?",
                response_text="RAG combines retrieval and generation...",
                category_path=["AI", "RAG"],
                query_vector=[0.1] * 1536,
                quality_score=0.85,
                usage_count=50,
                success_rate=0.90,
            ),
            CaseBank(
                case_id="test-case-002",
                query="Vector database comparison",
                response_text="ChromaDB, Pinecone, Weaviate comparison...",
                category_path=["Database", "Vector"],
                query_vector=[0.2] * 1536,
                quality_score=0.75,
                usage_count=30,
                success_rate=0.50,
            ),
            CaseBank(
                case_id="test-case-003",
                query="LLM fine-tuning best practices",
                response_text="Fine-tuning requires careful data preparation...",
                category_path=["AI", "LLM"],
                query_vector=[0.3] * 1536,
                quality_score=0.60,
                usage_count=10,
                success_rate=0.25,
            ),
            CaseBank(
                case_id="test-case-004",
                query="API authentication strategies",
                response_text="OAuth, JWT, API keys comparison...",
                category_path=["Security", "Auth"],
                query_vector=[0.4] * 1536,
                quality_score=0.95,
                usage_count=100,
                success_rate=0.98,
            ),
            CaseBank(
                case_id="test-case-005",
                query="Database indexing optimization",
                response_text="B-tree, Hash, GiST indexes explained...",
                category_path=["Database", "Performance"],
                query_vector=[0.5] * 1536,
                quality_score=0.70,
                usage_count=20,
                success_rate=0.60,
            ),
        ]

        for case in test_cases:
            db_session.add(case)

        await db_session.flush()  # Flush to DB but don't commit
        yield test_cases
        # Cleanup handled by transaction rollback
    except Exception as e:
        pytest.skip(f"Database not available: {e}")


@pytest.fixture
async def sample_execution_logs(db_session, sample_case_bank):
    """
    Create sample execution_log entries for Reflection tests
    @CODE:TEST-002:FIXTURE | SPEC: SPEC-TEST-002.md
    """
    try:
        from apps.api.database import ExecutionLog
        from datetime import datetime, timedelta
        from sqlalchemy import delete

        # Delete existing execution logs for test isolation
        await db_session.execute(
            delete(ExecutionLog).where(
                ExecutionLog.case_id.in_([
                    "test-case-001", "test-case-002", "test-case-003"
                ])
            )
        )
        await db_session.flush()

        logs = []

        # Case 001: High success rate (90%)
        for i in range(10):
            log = ExecutionLog(
                case_id="test-case-001",
                success=(i < 9),
                error_type="timeout" if i >= 9 else None,
                error_message="Request timeout" if i >= 9 else None,
                execution_time_ms=200 + i * 10,
                created_at=datetime.utcnow() - timedelta(hours=10-i)
            )
            db_session.add(log)
            logs.append(log)

        # Case 002: Medium success rate (50%)
        for i in range(10):
            log = ExecutionLog(
                case_id="test-case-002",
                success=(i % 2 == 0),
                error_type="validation_error" if i % 2 != 0 else None,
                error_message="Invalid input" if i % 2 != 0 else None,
                execution_time_ms=300 + i * 15,
                created_at=datetime.utcnow() - timedelta(hours=10-i)
            )
            db_session.add(log)
            logs.append(log)

        # Case 003: Low success rate (25%)
        for i in range(8):
            log = ExecutionLog(
                case_id="test-case-003",
                success=(i < 2),
                error_type="not_found" if i >= 2 else None,
                error_message="Resource not found" if i >= 2 else None,
                execution_time_ms=150 + i * 20,
                created_at=datetime.utcnow() - timedelta(hours=8-i)
            )
            db_session.add(log)
            logs.append(log)

        await db_session.flush()  # Flush to DB but don't commit
        yield logs
        # Cleanup handled by transaction rollback
    except Exception as e:
        pytest.skip(f"Database not available: {e}")


@pytest.fixture
async def async_client():
    """
    Create AsyncClient for API testing (Phase 3)
    @CODE:TEST-002:FIXTURE | SPEC: SPEC-TEST-002.md
    """
    from httpx import AsyncClient, ASGITransport
    from apps.api.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture(scope="session", autouse=True)
def validate_imports():
    """
    @TEST:CICD-001:FIXTURE | SPEC: SPEC-CICD-001.md | CODE: .claude/hooks/alfred/import-validator.py
    Validate Python imports before running any tests.

    This session-scoped fixture runs once at pytest initialization to catch
    import errors early, preventing test execution on broken code.

    Validation steps:
    1. compileall - Verify all Python files compile successfully
    2. API import - Ensure FastAPI application can be imported

    If validation fails, pytest exits immediately with a clear error message.

    HISTORY:
    v0.0.1 (2025-01-24): INITIAL - Phase 3 pytest fixture implementation
    """
    print("\n" + "=" * 60)
    print("🔍 Validating imports before test execution...")
    print("=" * 60)

    # Get project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Step 1: Validate Python syntax with compileall
    print("🔍 Step 1: Python syntax validation")
    result = subprocess.run(
        ["python3", "-m", "compileall", "-q", "apps/", "tests/"],
        cwd=project_root,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        error_msg = result.stderr.strip() if result.stderr else "Unknown compilation error"
        print("=" * 60)
        pytest.fail(
            f"❌ Import validation failed (compileall):\n{error_msg}",
            pytrace=False
        )

    print("✓ Python syntax validation passed")

    # Step 2: Validate API imports
    print("🔍 Step 2: API import validation")
    try:
        from apps.api.main import app
        print("✓ API imports validated")
    except ImportError as e:
        print("=" * 60)
        pytest.fail(
            f"❌ Import validation failed (API):\n{str(e)}",
            pytrace=False
        )

    print("=" * 60)
    print("✅ All imports validated successfully")
    print("=" * 60 + "\n")
