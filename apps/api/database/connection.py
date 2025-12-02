"""
Database connection management and type utilities.

Re-exports core database session components and provides
SQLite/PostgreSQL compatible type decorators.

@CODE:DATABASE-PKG-001
"""

from __future__ import annotations

import json
import uuid
from typing import Any, Optional, List

from sqlalchemy import String, Float, text
from sqlalchemy.types import TypeDecorator, TEXT
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSON

# Import core session components (to avoid circular imports)
from apps.core.db_session import engine, async_session, Base, DATABASE_URL

__all__ = [
    # Core session components
    "engine",
    "async_session",
    "Base",
    "DATABASE_URL",
    "get_async_session",
    "text",
    # Type utilities
    "JSONType",
    "ArrayType",
    "UUIDType",
    "get_json_type",
    "get_array_type",
    "get_vector_type",
    "get_uuid_type",
    "PGVECTOR_AVAILABLE",
]

# pgvector availability check
try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False


class JSONType(TypeDecorator[Any]):
    """SQLite-compatible JSON type decorator."""
    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Optional[str]:
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is not None:
            return json.loads(value)
        return value


class ArrayType(TypeDecorator[Any]):
    """SQLite-compatible Array type decorator."""
    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Optional[str]:
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is not None:
            return json.loads(value)
        return value


class UUIDType(TypeDecorator[uuid.UUID]):
    """SQLite-compatible UUID type decorator."""
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> Optional[str]:
        if value is not None:
            return str(value)
        return value

    def process_result_value(self, value: Any, dialect: Any) -> Optional[uuid.UUID]:
        if value is not None:
            return uuid.UUID(value)
        return value


def get_json_type() -> Any:
    """Get appropriate JSON type based on database."""
    if "sqlite" in DATABASE_URL:
        return JSONType()
    return JSON


def get_array_type(item_type: Any = String) -> Any:
    """Get appropriate Array type based on database."""
    if "sqlite" in DATABASE_URL:
        return ArrayType()
    return ARRAY(item_type)


def get_vector_type(dimensions: int = 1536) -> Any:
    """Get appropriate vector type based on database."""
    if "postgresql" in DATABASE_URL and PGVECTOR_AVAILABLE:
        from pgvector.sqlalchemy import Vector
        return Vector(dimensions)
    # SQLite fallback - use JSON array
    return get_array_type(Float)


def get_uuid_type() -> Any:
    """Get appropriate UUID type based on database."""
    if "sqlite" in DATABASE_URL:
        return UUIDType()
    return UUID(as_uuid=True)


async def get_async_session() -> Any:
    """
    FastAPI dependency for providing async database sessions.

    Usage:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_async_session)):
            ...
    """
    async with async_session() as session:
        yield session
