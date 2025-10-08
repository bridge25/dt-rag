import asyncio
from apps.core.db_session import async_session
from sqlalchemy import text

async def check_all_tables():
    async with async_session() as session:
        result = await session.execute(text("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname='public'
            ORDER BY tablename;
        """))
        tables = [row[0] for row in result.fetchall()]
        print(f"All tables in public schema ({len(tables)} total):")
        for table in tables:
            count_result = await session.execute(text(f"SELECT COUNT(*) FROM {table};"))
            count = count_result.scalar()
            print(f"  - {table}: {count} rows")

if __name__ == "__main__":
    asyncio.run(check_all_tables())
