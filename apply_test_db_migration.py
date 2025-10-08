"""Apply migration 0009 to test database directly"""
import asyncio
import asyncpg


async def apply_migration():
    """Apply migration 0009 to test database"""
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='postgres',
        database='dt_rag_test'
    )

    try:
        # Add missing columns to documents table
        await conn.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS title TEXT")
        print("✅ Added title column")

        await conn.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS content_type VARCHAR(100) DEFAULT 'text/plain'")
        print("✅ Added content_type column")

        await conn.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_size INTEGER")
        print("✅ Added file_size column")

        await conn.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS checksum VARCHAR(64)")
        print("✅ Added checksum column")

        await conn.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS doc_metadata JSONB DEFAULT '{}'")
        print("✅ Added doc_metadata column")

        await conn.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS chunk_metadata JSONB DEFAULT '{}'")
        print("✅ Added chunk_metadata column")

        await conn.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        print("✅ Added processed_at column")

        print("\n✅ All migrations applied successfully to test database")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        await conn.close()


if __name__ == '__main__':
    asyncio.run(apply_migration())
