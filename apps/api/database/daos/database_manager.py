"""
Database manager for connection and initialization.

@CODE:DATABASE-PKG-013
"""

from __future__ import annotations

import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..connection import engine, async_session, Base, DATABASE_URL

logger = logging.getLogger(__name__)

__all__ = ["DatabaseManager", "db_manager"]


class DatabaseManager:
    """Real PostgreSQL database manager."""

    def __init__(self) -> None:
        self.engine = engine
        self.async_session = async_session

    async def init_database(self) -> bool:
        """Initialize database and create tables."""
        try:
            async with self.engine.begin() as conn:
                # Install pgvector extension (PostgreSQL only)
                if "postgresql" in DATABASE_URL:
                    try:
                        await conn.execute(
                            text("CREATE EXTENSION IF NOT EXISTS vector")
                        )
                        logger.info("pgvector extension installed")
                    except Exception as e:
                        logger.warning(f"pgvector extension installation failed: {e}")

                # Create tables
                await conn.run_sync(Base.metadata.create_all)

            logger.info("Database initialization complete")
            return True

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            return False

    async def get_session(self) -> AsyncSession:
        """Return database session."""
        return self.async_session()

    async def test_connection(self) -> bool:
        """Test database connection."""
        try:
            async with self.async_session() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()
