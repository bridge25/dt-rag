"""Create database schema from SQLAlchemy models"""
import asyncio
import os
from sqlalchemy import create_engine, text

# Set DATABASE_URL
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://postgres:postgres@localhost:5432/dt_rag'

async def create_schema():
    """Create all tables from models"""
    # Import Base after setting DATABASE_URL
    from apps.api.database import Base

    # Create sync engine for schema creation
    database_url = os.getenv('DATABASE_URL', '').replace('postgresql+asyncpg', 'postgresql+psycopg2')
    engine = create_engine(database_url)

    print(f"Creating schema on: {database_url}")

    # Create pgvector extension first
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
        print("[OK] pgvector extension enabled")

    # Create all tables
    Base.metadata.create_all(engine)
    print(f"[OK] Created {len(Base.metadata.sorted_tables)} tables:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")

    engine.dispose()
    print("\nSchema creation complete!")

if __name__ == '__main__':
    asyncio.run(create_schema())
