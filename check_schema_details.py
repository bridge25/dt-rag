#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check detailed database schema to verify doc_metadata column exists
"""
import asyncio
import sqlite3
import sys
from pathlib import Path

# UTF-8 encoding setup for Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "apps" / "api"))

async def check_sqlite_schema():
    """Check SQLite schema directly"""
    try:
        conn = sqlite3.connect("dt_rag_test.db")
        cursor = conn.cursor()

        # Get taxonomy_nodes table schema
        cursor.execute("PRAGMA table_info(taxonomy_nodes)")
        columns = cursor.fetchall()

        print("taxonomy_nodes 테이블 컬럼 정보:")
        print("-" * 50)
        for column in columns:
            cid, name, type_, notnull, default_value, pk = column
            print(f"  {name}: {type_} (null={not notnull}, default={default_value}, pk={pk})")

        # Check if doc_metadata exists
        doc_metadata_exists = any(col[1] == 'doc_metadata' for col in columns)
        print(f"\ndoc_metadata 컬럼 존재: {doc_metadata_exists}")

        # Check embeddings table for vector column
        cursor.execute("PRAGMA table_info(embeddings)")
        embed_columns = cursor.fetchall()

        print("\nembeddings 테이블 컬럼 정보:")
        print("-" * 50)
        for column in embed_columns:
            cid, name, type_, notnull, default_value, pk = column
            print(f"  {name}: {type_} (null={not notnull}, default={default_value}, pk={pk})")

        conn.close()
        return doc_metadata_exists

    except Exception as e:
        print(f"❌ 스키마 확인 실패: {e}")
        return False

async def check_database_schema():
    """Check database schema using SQLAlchemy"""
    try:
        from database import engine, async_session
        from sqlalchemy import text, inspect

        # Check current database type
        from database import DATABASE_URL
        print(f"데이터베이스 URL: {DATABASE_URL}")

        async with engine.begin() as conn:
            # Get table schema info
            inspector = await conn.run_sync(lambda sync_conn: inspect(sync_conn))
            tables = await conn.run_sync(lambda sync_conn: inspector.get_table_names())

            print(f"\n현재 테이블 목록: {tables}")

            if 'taxonomy_nodes' in tables:
                columns = await conn.run_sync(
                    lambda sync_conn: inspector.get_columns('taxonomy_nodes')
                )

                print("\ntaxonomy_nodes 컬럼 정보 (SQLAlchemy):")
                print("-" * 60)
                for col in columns:
                    print(f"  {col['name']}: {col['type']} (nullable={col['nullable']})")

                # Check if doc_metadata exists
                doc_metadata_exists = any(col['name'] == 'doc_metadata' for col in columns)
                print(f"\ndoc_metadata 컬럼 존재: {doc_metadata_exists}")

                return doc_metadata_exists
            else:
                print("taxonomy_nodes 테이블이 존재하지 않음")
                return False

    except Exception as e:
        print(f"❌ SQLAlchemy 스키마 확인 실패: {e}")
        return False

async def test_vector_operations():
    """Test vector operations compatibility"""
    try:
        from database import async_session, SearchDAO
        from sqlalchemy import text

        print("\nVector 연산 호환성 테스트...")

        async with async_session() as session:
            # Try to execute a sample vector query (SQLite version)
            try:
                # This should work with SQLite
                query = text("""
                    SELECT 1 as test_result
                    FROM embeddings
                    WHERE vec IS NOT NULL
                    LIMIT 1
                """)
                result = await session.execute(query)
                print("기본 벡터 쿼리 성공")

                # Test the problematic <=> operator
                try:
                    query_with_operator = text("""
                        SELECT 1.0 - (e.vec <=> :query_vector) as similarity
                        FROM embeddings e
                        WHERE e.vec IS NOT NULL
                        LIMIT 1
                    """)
                    # This will likely fail in SQLite
                    result = await session.execute(query_with_operator, {"query_vector": "[1,2,3]"})
                    print("<=> 연산자 지원됨")
                except Exception as e:
                    print(f"<=> 연산자 실패 (예상됨): {str(e)[:100]}...")

            except Exception as e:
                print(f"벡터 쿼리 실패: {e}")

    except Exception as e:
        print(f"Vector 연산 테스트 실패: {e}")

async def main():
    """Main test function"""
    print("Database Schema Critical Issues 검증")
    print("=" * 60)

    # Test 1: Check doc_metadata column
    print("\n1. doc_metadata 컬럼 검증...")
    await check_sqlite_schema()

    # Test 2: SQLAlchemy schema check
    print("\n2. SQLAlchemy 스키마 검증...")
    await check_database_schema()

    # Test 3: Vector operations compatibility
    print("\n3. Vector 연산 호환성 검증...")
    await test_vector_operations()

    print("\n" + "=" * 60)
    print("Critical Issues 검증 완료")

if __name__ == "__main__":
    asyncio.run(main())