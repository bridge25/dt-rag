import asyncio
from apps.core.db_session import async_session
from sqlalchemy import text

async def test():
    try:
        async with async_session() as session:
            result = await session.execute(text('SELECT 1'))
            print('DB connection successful:', result.scalar())
    except Exception as e:
        print('DB connection failed:', e)

asyncio.run(test())
