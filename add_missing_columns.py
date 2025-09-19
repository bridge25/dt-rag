#!/usr/bin/env python3
"""
Add missing columns to the database for hybrid search
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

from apps.api.database import db_manager
from sqlalchemy import text

async def main():
    """Add missing columns"""
    try:
        print("Adding missing columns for hybrid search...")

        async with db_manager.async_session() as session:
            # Add doc_metadata column to documents table
            try:
                await session.execute(text("""
                    ALTER TABLE documents
                    ADD COLUMN doc_metadata TEXT DEFAULT '{}'
                """))
                print("[OK] Added doc_metadata column to documents table")
            except Exception as e:
                print(f"[INFO] doc_metadata column may already exist: {e}")

            # Add embedding column to chunks table
            try:
                await session.execute(text("""
                    ALTER TABLE chunks
                    ADD COLUMN embedding TEXT
                """))
                print("[OK] Added embedding column to chunks table")
            except Exception as e:
                print(f"[INFO] embedding column may already exist: {e}")

            await session.commit()

        print("[OK] Database schema updated successfully!")
        return True

    except Exception as e:
        print(f"[ERROR] Schema update failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)