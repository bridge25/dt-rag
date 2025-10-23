import asyncio
from apps.core.db_session import engine
from sqlalchemy import text

async def check_tables():
    async with engine.begin() as conn:
        result = await conn.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
        ))
        tables = [row[0] for row in result]
        print("Existing tables:")
        for table in tables:
            print(f"  - {table}")

asyncio.run(check_tables())
