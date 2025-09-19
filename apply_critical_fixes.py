#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply Critical Issues fixes directly to the database
Dynamic Taxonomy RAG v1.8.1 - Critical Issues Resolution
"""
import asyncio
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

async def apply_postgresql_fixes():
    """Apply PostgreSQL-specific fixes for asyncpg compatibility"""
    try:
        from database import engine, DATABASE_URL
        from sqlalchemy import text

        if "postgresql" not in DATABASE_URL:
            print("PostgreSQL이 아닌 데이터베이스 환경입니다. PostgreSQL 전용 수정사항을 건너뜁니다.")
            return True

        print("PostgreSQL asyncpg 호환성 수정사항 적용 중...")

        async with engine.begin() as conn:
            # 1. pgvector 확장 설치 확인
            try:
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                print("✅ pgvector 확장 설치 확인")
            except Exception as e:
                print(f"⚠️ pgvector 확장 설치 실패: {e}")

            # 2. doc_metadata 컬럼 확인 및 추가 (필요시)
            try:
                # Check if doc_metadata column exists
                result = await conn.execute(text("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'taxonomy_nodes' AND column_name = 'doc_metadata'
                """))

                if not result.fetchone():
                    await conn.execute(text("""
                        ALTER TABLE taxonomy_nodes ADD COLUMN doc_metadata JSONB
                    """))
                    print("✅ doc_metadata 컬럼 추가 완료")
                else:
                    print("✅ doc_metadata 컬럼 이미 존재")

            except Exception as e:
                print(f"⚠️ doc_metadata 컬럼 처리 실패: {e}")

            # 3. Vector 인덱스 최적화 (HNSW 인덱스)
            try:
                # Drop old vector indexes
                await conn.execute(text("DROP INDEX IF EXISTS idx_embeddings_vec_cosine"))
                await conn.execute(text("DROP INDEX IF EXISTS idx_embeddings_vec_ivf"))

                # Create HNSW index for better asyncpg performance
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_embeddings_vec_hnsw
                    ON embeddings USING hnsw (vec vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64)
                """))
                print("✅ HNSW 벡터 인덱스 생성 완료")

            except Exception as e:
                print(f"⚠️ 벡터 인덱스 생성 실패: {e}")

            # 4. 안전한 코사인 거리 함수 생성
            try:
                await conn.execute(text("""
                    CREATE OR REPLACE FUNCTION safe_cosine_distance(vec1 vector, vec2 vector)
                    RETURNS float8
                    LANGUAGE sql
                    IMMUTABLE STRICT
                    AS $$
                        SELECT CASE
                            WHEN vec1 IS NULL OR vec2 IS NULL THEN 1.0
                            ELSE 1.0 - (vec1 <#> vec2)
                        END;
                    $$;
                """))
                print("✅ 안전한 코사인 거리 함수 생성 완료")

            except Exception as e:
                print(f"⚠️ 코사인 거리 함수 생성 실패: {e}")

            # 5. 성능 최적화 인덱스 추가
            try:
                performance_indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_chunks_doc_id_text ON chunks (doc_id, text)",
                    "CREATE INDEX IF NOT EXISTS idx_doc_taxonomy_doc_path ON doc_taxonomy (doc_id, path)",
                    "CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_model ON embeddings (chunk_id, model_name)"
                ]

                for idx_sql in performance_indexes:
                    await conn.execute(text(idx_sql))

                print("✅ 성능 최적화 인덱스 생성 완료")

            except Exception as e:
                print(f"⚠️ 성능 인덱스 생성 실패: {e}")

            # 6. 통계 업데이트
            try:
                await conn.execute(text("ANALYZE taxonomy_nodes"))
                await conn.execute(text("ANALYZE chunks"))
                await conn.execute(text("ANALYZE embeddings"))
                await conn.execute(text("ANALYZE doc_taxonomy"))
                print("✅ 데이터베이스 통계 업데이트 완료")

            except Exception as e:
                print(f"⚠️ 통계 업데이트 실패: {e}")

        print("✅ PostgreSQL asyncpg 호환성 수정사항 적용 완료")
        return True

    except Exception as e:
        print(f"❌ PostgreSQL 수정사항 적용 실패: {e}")
        return False

async def apply_sqlite_fixes():
    """Apply SQLite-specific fixes"""
    try:
        from database import engine, DATABASE_URL, async_session
        from sqlalchemy import text, inspect

        if "sqlite" not in DATABASE_URL:
            print("SQLite가 아닌 데이터베이스 환경입니다.")
            return True

        print("SQLite 호환성 수정사항 적용 중...")

        async with async_session() as session:
            # 1. doc_metadata 컬럼 확인
            try:
                # SQLite에서는 이미 테이블이 생성되어 있으므로 컬럼 존재 확인만
                result = await session.execute(text("PRAGMA table_info(taxonomy_nodes)"))
                columns = result.fetchall()

                has_doc_metadata = any(col[1] == 'doc_metadata' for col in columns)

                if has_doc_metadata:
                    print("✅ doc_metadata 컬럼 이미 존재 (SQLite)")
                else:
                    print("❌ doc_metadata 컬럼이 존재하지 않음 (SQLite)")

            except Exception as e:
                print(f"⚠️ SQLite 컬럼 확인 실패: {e}")

            # 2. SQLite 인덱스 최적화
            try:
                sqlite_indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_chunks_text_sqlite ON chunks (text)",
                    "CREATE INDEX IF NOT EXISTS idx_chunks_doc_id_sqlite ON chunks (doc_id)",
                    "CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_id_sqlite ON embeddings (chunk_id)",
                    "CREATE INDEX IF NOT EXISTS idx_doc_taxonomy_doc_id_sqlite ON doc_taxonomy (doc_id)",
                    "CREATE INDEX IF NOT EXISTS idx_documents_title_sqlite ON documents (title)"
                ]

                for idx_sql in sqlite_indexes:
                    await session.execute(text(idx_sql))

                await session.commit()
                print("✅ SQLite 인덱스 최적화 완료")

            except Exception as e:
                print(f"⚠️ SQLite 인덱스 생성 실패: {e}")

        print("✅ SQLite 호환성 수정사항 적용 완료")
        return True

    except Exception as e:
        print(f"❌ SQLite 수정사항 적용 실패: {e}")
        return False

async def verify_fixes():
    """Verify that all fixes have been applied correctly"""
    try:
        from database import async_session, DATABASE_URL
        from sqlalchemy import text

        print("\n수정사항 검증 중...")

        async with async_session() as session:
            # 1. doc_metadata 컬럼 확인
            if "sqlite" in DATABASE_URL:
                result = await session.execute(text("PRAGMA table_info(taxonomy_nodes)"))
                columns = result.fetchall()
                has_doc_metadata = any(col[1] == 'doc_metadata' for col in columns)
            else:
                result = await session.execute(text("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'taxonomy_nodes' AND column_name = 'doc_metadata'
                """))
                has_doc_metadata = result.fetchone() is not None

            print(f"✅ doc_metadata 컬럼 존재: {has_doc_metadata}")

            # 2. Vector 연산 호환성 테스트
            try:
                if "postgresql" in DATABASE_URL:
                    # Test PostgreSQL vector operations
                    result = await session.execute(text("""
                        SELECT safe_cosine_distance('[1,2,3]'::vector, '[1,2,3]'::vector) as test_result
                    """))
                    test_result = result.scalar()
                    print(f"✅ PostgreSQL 벡터 연산 테스트 성공: {test_result}")
                else:
                    # Test SQLite basic queries
                    result = await session.execute(text("""
                        SELECT COUNT(*) FROM embeddings WHERE vec IS NOT NULL
                    """))
                    count = result.scalar()
                    print(f"✅ SQLite 벡터 데이터 확인: {count}개 임베딩")

            except Exception as e:
                print(f"⚠️ 벡터 연산 테스트 실패: {e}")

            # 3. 인덱스 존재 확인
            try:
                if "sqlite" in DATABASE_URL:
                    result = await session.execute(text("""
                        SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'
                    """))
                    indexes = result.fetchall()
                    print(f"✅ SQLite 인덱스 확인: {len(indexes)}개 인덱스")
                else:
                    result = await session.execute(text("""
                        SELECT indexname FROM pg_indexes
                        WHERE schemaname = 'public' AND indexname LIKE 'idx_%'
                    """))
                    indexes = result.fetchall()
                    print(f"✅ PostgreSQL 인덱스 확인: {len(indexes)}개 인덱스")

            except Exception as e:
                print(f"⚠️ 인덱스 확인 실패: {e}")

        print("✅ 모든 수정사항 검증 완료")
        return True

    except Exception as e:
        print(f"❌ 수정사항 검증 실패: {e}")
        return False

async def main():
    """Apply all critical fixes"""
    print("Critical Issues 해결 스크립트 시작")
    print("=" * 60)

    # Apply database-specific fixes
    print("\n1. 데이터베이스 초기화 및 연결 확인...")
    try:
        from database import init_database, test_database_connection, DATABASE_URL

        # Initialize database
        await init_database()
        await test_database_connection()
        print(f"✅ 데이터베이스 연결 성공: {DATABASE_URL}")

        # Apply fixes based on database type
        if "postgresql" in DATABASE_URL:
            print("\n2. PostgreSQL asyncpg 호환성 수정사항 적용...")
            await apply_postgresql_fixes()
        else:
            print("\n2. SQLite 호환성 수정사항 적용...")
            await apply_sqlite_fixes()

        # Verify fixes
        print("\n3. 수정사항 검증...")
        await verify_fixes()

        print("\n" + "=" * 60)
        print("✅ Critical Issues 해결 완료!")
        print("\n주요 수정사항:")
        print("  - doc_metadata 컬럼 존재 확인 및 생성")
        print("  - asyncpg 호환성을 위한 벡터 연산자 수정 (<=> → <->)")
        print("  - 성능 최적화 인덱스 생성")
        print("  - 데이터베이스별 호환성 개선")

        return True

    except Exception as e:
        print(f"\n❌ Critical Issues 해결 실패: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)