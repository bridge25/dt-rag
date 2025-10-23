import asyncio
from apps.core.db_session import async_session
from sqlalchemy import text

async def main():
    async with async_session() as session:
        result = await session.execute(text('SELECT COUNT(*) FROM documents'))
        print('Documents:', result.scalar())

        result = await session.execute(text('SELECT COUNT(*) FROM chunks'))
        print('Chunks:', result.scalar())

        result = await session.execute(text('SELECT COUNT(*) FROM embeddings'))
        print('Embeddings:', result.scalar())

        result = await session.execute(text(
            "SELECT substring(c.text, 1, 100) as text_sample, e.vec IS NOT NULL as has_vec "
            "FROM chunks c LEFT JOIN embeddings e ON c.chunk_id = e.chunk_id LIMIT 3"
        ))
        print('\nChunk samples:')
        for row in result:
            print(f'  Text: {row[0][:50]}... Has vector: {row[1]}')

asyncio.run(main())
