import asyncio
from apps.core.db_session import async_session
from sqlalchemy import text

async def main():
    async with async_session() as s:
        r = await s.execute(text('SELECT COUNT(*) FROM documents'))
        print(f'Documents: {r.scalar()}')
        r2 = await s.execute(text('SELECT COUNT(*) FROM chunks'))
        print(f'Chunks: {r2.scalar()}')

asyncio.run(main())
