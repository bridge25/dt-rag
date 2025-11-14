#!/usr/bin/env python3
"""
Install pgvector extension in Railway PostgreSQL database.
Run this before alembic migrations.
"""

import asyncio
import asyncpg
import os
import sys


async def install_pgvector():
    """Install pgvector extension if not already installed."""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)

    # Convert SQLAlchemy URL to asyncpg URL
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

    try:
        print("Connecting to PostgreSQL database...")
        conn = await asyncpg.connect(database_url)

        try:
            print("Installing pgvector extension...")
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            print("✓ pgvector extension created successfully")

            # Verify installation
            result = await conn.fetch(
                "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
            )

            if result:
                version = result[0]["extversion"]
                print(f"✓ pgvector version: {version}")
            else:
                print("WARNING: pgvector extension not found after installation")

        finally:
            await conn.close()
            print("Database connection closed")

    except Exception as e:
        print(f"ERROR: Failed to install pgvector extension: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(install_pgvector())
