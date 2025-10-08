"""Step-by-step PostgreSQL test"""
import asyncio
import os
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://postgres:postgres@localhost:5433/dt_rag_test'

from sqlalchemy import text
from apps.core.db_session import engine, Base

# Import models to register them
from apps.api.database import Document, DocumentChunk, Embedding, DocTaxonomy, TaxonomyNode

async def step1_extension():
    print("Step 1: Creating vector extension...")
    async with engine.begin() as conn:
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
    print("SUCCESS: Vector extension created")

async def step2_tables():
    print("Step 2: Creating tables...")
    print(f"  Base.metadata has {len(Base.metadata.tables)} tables registered:")
    for table_name in Base.metadata.tables.keys():
        print(f"    - {table_name}")

    if len(Base.metadata.tables) == 0:
        print("  ERROR: No tables registered in Base.metadata!")
        print("  Need to import model classes first")
        return

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            # engine.begin() automatically commits on exit
        print("SUCCESS: Tables created (transaction committed)")
    except Exception as e:
        print(f"ERROR creating tables: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return

async def step3_check_tables():
    print("Step 3: Checking tables...")
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        tables = result.fetchall()
        print(f"Found {len(tables)} tables: {[t[0] for t in tables]}")

async def main():
    try:
        await step1_extension()
    except Exception as e:
        print(f"FAIL Step 1: {type(e).__name__}: {e}")
        return

    try:
        await step2_tables()
    except Exception as e:
        print(f"FAIL Step 2: {type(e).__name__}: {e}")
        return

    try:
        await step3_check_tables()
    except Exception as e:
        print(f"FAIL Step 3: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
