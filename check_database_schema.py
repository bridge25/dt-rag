#!/usr/bin/env python3
"""
Check actual database schema to see what columns exist
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

from apps.api.database import db_manager
from sqlalchemy import text

async def main():
    """Check database schema"""
    try:
        print("Checking database schema...")

        async with db_manager.async_session() as session:
            # Check documents table schema
            result = await session.execute(text("PRAGMA table_info(documents)"))
            rows = result.fetchall()

            print("\nDocuments table columns:")
            for row in rows:
                print(f"  {row[1]} ({row[2]})")

            # Check chunks table schema
            result = await session.execute(text("PRAGMA table_info(chunks)"))
            rows = result.fetchall()

            print("\nChunks table columns:")
            for row in rows:
                print(f"  {row[1]} ({row[2]})")

        return True

    except Exception as e:
        print(f"[ERROR] Schema check failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)