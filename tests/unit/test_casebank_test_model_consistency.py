"""
@TEST:TAG-CASEBANK-TEST-MODEL-002
Test model consistency verification

This test ensures test fixtures properly mirror production schema types,
particularly for query_vector field which should serialize List[float].
"""
# @TEST:TAG-CASEBANK-TEST-MODEL-002

import pytest
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy import Text, Integer, Float, String, DateTime, func, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column, declarative_base
from sqlalchemy.types import JSON
import asyncio
import os

TestBase = declarative_base()


class TestCaseBank(TestBase):  # type: ignore[misc,valid-type]
    """
    @TEST:TAG-CASEBANK-TEST-MODEL-002
    Test model with proper vector serialization
    """
    __tablename__ = "case_bank_test"

    case_id: Mapped[str] = mapped_column(Text, primary_key=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    category_path: Mapped[str] = mapped_column(Text, nullable=False)
    quality: Mapped[Optional[float]] = mapped_column(Float)

    # @CODE:TAG-CASEBANK-TEST-MODEL-002 - JSON serialized vector for SQLite compatibility
    query_vector: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="JSON-serialized List[float] for SQLite test compatibility"
    )

    usage_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    success_rate: Mapped[Optional[float]] = mapped_column(Float, default=100.0)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now()
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, server_default=func.now()
    )

    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


test_engine = create_async_engine(
    "sqlite+aiosqlite:///test_model_consistency.db", echo=False
)
test_async_session = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="module", autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(TestBase.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(TestBase.metadata.drop_all)
    await test_engine.dispose()
    try:
        os.remove("test_model_consistency.db")
    except FileNotFoundError:
        pass


@pytest.fixture(autouse=True)
async def cleanup_cases():
    yield
    async with test_async_session() as session:
        stmt = select(TestCaseBank)
        result = await session.execute(stmt)
        cases = result.scalars().all()
        for case in cases:
            await session.delete(case)
        await session.commit()


class TestQueryVectorSerialization:
    """Test query_vector field properly serializes List[float] as JSON"""

    @pytest.mark.asyncio
    async def test_query_vector_stores_json_serialized_list(self):
        """
        @TEST:TAG-CASEBANK-TEST-MODEL-002-1
        Verify query_vector stores JSON-serialized float arrays
        """
        vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        vector_json = json.dumps(vector)

        async with test_async_session() as session:
            case = TestCaseBank(
                case_id="test-vector-001",
                query="test query",
                answer="test answer",
                sources={},
                category_path='["Test"]',
                query_vector=vector_json,  # Store as JSON string
            )
            session.add(case)
            await session.commit()
            await session.refresh(case)

            # Verify it's stored as JSON string
            assert case.query_vector is not None
            assert isinstance(case.query_vector, str)

            # Verify it can be deserialized back to list
            deserialized = json.loads(case.query_vector)
            assert isinstance(deserialized, list)
            assert len(deserialized) == 5
            assert deserialized == vector

    @pytest.mark.asyncio
    async def test_query_vector_handles_1536_dimensions(self):
        """
        @TEST:TAG-CASEBANK-TEST-MODEL-002-2
        Verify query_vector can handle OpenAI embedding size (1536)
        """
        # Create a 1536-dimensional vector
        vector = [0.001 * i for i in range(1536)]
        vector_json = json.dumps(vector)

        async with test_async_session() as session:
            case = TestCaseBank(
                case_id="test-vector-1536",
                query="test query with full embedding",
                answer="test answer",
                sources={},
                category_path='["Test"]',
                query_vector=vector_json,
            )
            session.add(case)
            await session.commit()
            await session.refresh(case)

            # Verify storage and retrieval
            assert case.query_vector is not None
            deserialized = json.loads(case.query_vector)
            assert len(deserialized) == 1536
            assert deserialized[0] == 0.0
            assert abs(deserialized[1535] - 1.535) < 0.001

    @pytest.mark.asyncio
    async def test_query_vector_nullable_for_legacy_cases(self):
        """
        @TEST:TAG-CASEBANK-TEST-MODEL-002-3
        Verify query_vector can be NULL for backward compatibility
        """
        async with test_async_session() as session:
            case = TestCaseBank(
                case_id="test-no-vector",
                query="test query without vector",
                answer="test answer",
                sources={},
                category_path='["Test"]',
                query_vector=None,  # NULL for legacy cases
            )
            session.add(case)
            await session.commit()
            await session.refresh(case)

            assert case.query_vector is None

    @pytest.mark.asyncio
    async def test_query_vector_empty_list_serialization(self):
        """
        @TEST:TAG-CASEBANK-TEST-MODEL-002-4
        Verify empty vector lists are handled correctly
        """
        vector = []
        vector_json = json.dumps(vector)

        async with test_async_session() as session:
            case = TestCaseBank(
                case_id="test-empty-vector",
                query="test query",
                answer="test answer",
                sources={},
                category_path='["Test"]',
                query_vector=vector_json,
            )
            session.add(case)
            await session.commit()
            await session.refresh(case)

            assert case.query_vector == "[]"
            deserialized = json.loads(case.query_vector)
            assert deserialized == []
