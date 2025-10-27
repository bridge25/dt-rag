"""
Database session and engine management
순환 참조 방지를 위한 순수 DB 연결 계층
"""

import os
import logging
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/dt_rag"
)

logger.info(f"Database URL: {DATABASE_URL}")

if "sqlite" in DATABASE_URL.lower():
    if "aiosqlite" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
        logger.info(f"Updated DATABASE_URL to use aiosqlite: {DATABASE_URL}")

    engine = create_async_engine(
        DATABASE_URL, echo=False, connect_args={"check_same_thread": False}
    )
    logger.info("Created SQLite engine with aiosqlite driver")
else:
    engine = create_async_engine(DATABASE_URL, echo=False)
    logger.info("Created PostgreSQL engine with asyncpg driver")

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()
