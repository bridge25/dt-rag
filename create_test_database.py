#!/usr/bin/env python3
"""
Create test database with updated schema for hybrid search
"""
import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

from apps.api.database import db_manager, Base, engine

async def main():
    """Create database tables"""
    try:
        print("Creating database tables...")

        # Create all tables from models
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        print("[OK] Database tables created successfully!")

        # Test connection
        connection_ok = await db_manager.test_connection()
        if connection_ok:
            print("[OK] Database connection test passed!")
        else:
            print("[ERROR] Database connection test failed!")
            return False

        return True

    except Exception as e:
        print(f"[ERROR] Error creating database: {e}")
        logging.exception("Database creation failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)