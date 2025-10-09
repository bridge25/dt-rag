"""Initialize test database with proper schema"""
import asyncio
import asyncpg
from pathlib import Path


async def init_test_database():
    """Initialize test database from init.sql"""
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='postgres',
        database='dt_rag_test'
    )

    try:
        # Read init.sql
        init_sql_path = Path(__file__).parent / 'init.sql'
        init_sql = init_sql_path.read_text()

        # Execute init.sql
        await conn.execute(init_sql)
        print("✅ Test database initialized successfully")

    except Exception as e:
        print(f"❌ Failed to initialize test database: {e}")
        raise
    finally:
        await conn.close()


if __name__ == '__main__':
    asyncio.run(init_test_database())
