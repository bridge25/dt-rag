"""Reset test database completely"""
import asyncio
import asyncpg


async def reset_test_database():
    """Drop all tables in test database"""
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='postgres',
        database='dt_rag_test'
    )

    try:
        # Drop all tables
        await conn.execute("""
            DROP SCHEMA public CASCADE;
            CREATE SCHEMA public;
            GRANT ALL ON SCHEMA public TO postgres;
            GRANT ALL ON SCHEMA public TO public;
            CREATE EXTENSION IF NOT EXISTS vector;
        """)
        print("✅ Test database reset successfully")

    except Exception as e:
        print(f"❌ Failed to reset test database: {e}")
        raise
    finally:
        await conn.close()


if __name__ == '__main__':
    asyncio.run(reset_test_database())
