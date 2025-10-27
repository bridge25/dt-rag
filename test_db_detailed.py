import asyncio
import os
import logging

logging.basicConfig(level=logging.DEBUG)

os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/dt_rag_test"

from apps.core.db_session import async_session, engine
from sqlalchemy import text

async def test():
    print("Starting DB connection test...")
    print(f"Database URL: {os.getenv('DATABASE_URL')}")

    try:
        print("Creating session...")
        async with async_session() as session:
            print("Session created, executing query...")
            result = await asyncio.wait_for(
                session.execute(text('SELECT 1 as test_value')),
                timeout=3.0
            )
            value = result.scalar()
            print(f'DB connection successful: {value}')
    except asyncio.TimeoutError:
        print('DB connection TIMEOUT after 3 seconds')
    except Exception as e:
        print(f'DB connection FAILED: {type(e).__name__}: {e}')
    finally:
        print("Disposing engine...")
        await engine.dispose()
        print("Test complete.")

asyncio.run(test())
