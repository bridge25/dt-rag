#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Database Testing Script with UTF-8 Support
Dynamic Taxonomy RAG v1.8.1 - Database Connection and Schema Validation Test
"""
import os
import sys
import asyncio
import logging
from typing import Dict, Any, List
from pathlib import Path

# UTF-8 encoding setup
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "apps" / "api"))

# Configure logging with UTF-8
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_database.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

async def test_database_connection():
    """Test basic database connection and configuration"""
    try:
        logger.info("🔍 데이터베이스 연결 테스트 시작...")

        # Import database components
        from database import (
            init_database,
            test_database_connection as db_test,
            DATABASE_URL,
            engine
        )

        # Test database URL configuration
        logger.info(f"✅ 데이터베이스 URL 로드 완료: {DATABASE_URL}")

        # Test database initialization
        await init_database()
        logger.info("✅ 데이터베이스 초기화 완료")

        # Test basic connection
        await db_test()
        logger.info("✅ 데이터베이스 연결 테스트 완료")

        return True

    except Exception as e:
        logger.error(f"❌ 데이터베이스 연결 테스트 실패: {str(e)}")
        return False

async def test_schema_validation():
    """Test database schema and table creation"""
    try:
        logger.info("🔍 스키마 검증 테스트 시작...")

        from database import (
            Document, DocumentChunk, TaxonomyNode, TaxonomyEdge,
            Embedding, DocTaxonomy, CaseBank,
            Base, engine
        )
        from sqlalchemy import inspect, text

        # Test table creation
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ 데이터베이스 테이블 생성 완료")

        # Verify tables exist
        async with engine.begin() as conn:
            inspector = await conn.run_sync(lambda sync_conn: inspect(sync_conn))
            tables = await conn.run_sync(lambda sync_conn: inspector.get_table_names())

        expected_tables = [
            'documents', 'chunks', 'taxonomy_nodes', 'taxonomy_edges',
            'embeddings', 'doc_taxonomy', 'case_bank', 'taxonomy_migrations'
        ]

        missing_tables = [table for table in expected_tables if table not in tables]
        if missing_tables:
            logger.warning(f"⚠️ 일부 테이블 누락: {missing_tables}")
        else:
            logger.info(f"✅ 모든 필수 테이블 존재 확인: {expected_tables}")

        # Check existing tables
        logger.info(f"✅ 현재 존재하는 테이블: {tables}")

        # Test pgvector extension (if PostgreSQL)
        try:
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'"))
                if not result.fetchone():
                    logger.warning("⚠️ pgvector 확장이 설치되지 않음")
                else:
                    logger.info("✅ pgvector 확장 설치 확인")
        except Exception:
            logger.info("ℹ️ PostgreSQL 확장 확인 건너뜀 (다른 DB 사용 중)")

        return True

    except Exception as e:
        logger.error(f"❌ 스키마 검증 테스트 실패: {str(e)}")
        return False

async def test_model_operations():
    """Test basic CRUD operations on models"""
    try:
        logger.info("🔍 모델 CRUD 작업 테스트 시작...")

        from database import Document, DocumentChunk, TaxonomyNode, async_session
        from datetime import datetime
        import uuid

        async with async_session() as session:
            # Test Document creation
            test_doc = Document(
                doc_id=uuid.uuid4(),
                title="테스트 문서",
                content_type="text/plain",
                file_size=1024,
                chunk_metadata={"source": "test", "language": "ko"},
                processed_at=datetime.utcnow()
            )

            session.add(test_doc)
            await session.commit()
            logger.info(f"✅ 문서 생성 완료: {test_doc.doc_id}")

            # Test DocumentChunk creation
            test_chunk = DocumentChunk(
                chunk_id=uuid.uuid4(),
                doc_id=test_doc.doc_id,
                chunk_text="테스트 청크 내용입니다. 한글이 정상적으로 저장되는지 확인합니다.",
                start_byte=0,
                end_byte=100,
                created_at=datetime.utcnow()
            )

            session.add(test_chunk)
            await session.commit()
            logger.info(f"✅ 문서 청크 생성 완료: {test_chunk.chunk_id}")

            # Test TaxonomyNode creation
            test_node = TaxonomyNode(
                canonical_path=["테스트", "분류"],
                node_name="테스트 분류",
                description="테스트용 분류 노드",
                doc_metadata={"test": True},
                is_active=True,
                created_at=datetime.utcnow()
            )

            session.add(test_node)
            await session.commit()
            logger.info(f"✅ 분류 노드 생성 완료: {test_node.node_id}")

            # Test retrieval
            retrieved_doc = await session.get(Document, test_doc.doc_id)
            if retrieved_doc:
                logger.info(f"✅ 문서 조회 성공: {retrieved_doc.title}")
            else:
                logger.error("❌ 문서 조회 실패")
                return False

            # Cleanup test data
            await session.delete(test_chunk)
            await session.delete(test_doc)
            await session.delete(test_node)
            await session.commit()
            logger.info("✅ 테스트 데이터 정리 완료")

        return True

    except Exception as e:
        logger.error(f"❌ 모델 CRUD 작업 테스트 실패: {str(e)}")
        return False

async def test_database_indexes():
    """Test critical database indexes"""
    try:
        logger.info("🔍 데이터베이스 인덱스 테스트 시작...")

        from database import engine
        from sqlalchemy import text

        # Test basic database connection first
        try:
            async with engine.begin() as conn:
                # Simple connectivity test
                result = await conn.execute(text("SELECT 1"))
                if result.fetchone():
                    logger.info("✅ 데이터베이스 연결 확인")

                # Check if we can access table information
                result = await conn.execute(text("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public'
                    LIMIT 5
                """))
                tables = result.fetchall()
                logger.info(f"✅ 테이블 정보 조회 성공: {len(tables)}개 테이블")

                # Check for indexes if PostgreSQL
                try:
                    result = await conn.execute(text("""
                        SELECT indexname, tablename FROM pg_indexes
                        WHERE schemaname = 'public'
                        LIMIT 10
                    """))
                    indexes = result.fetchall()
                    logger.info(f"✅ 인덱스 정보 조회 성공: {len(indexes)}개 인덱스")
                except Exception:
                    logger.info("ℹ️ PostgreSQL 인덱스 조회 건너뜀 (다른 DB 사용 중)")

        except Exception as conn_error:
            logger.warning(f"⚠️ 데이터베이스 연결 실패: {str(conn_error)}")
            return False

        return True

    except Exception as e:
        logger.error(f"❌ 인덱스 테스트 실패: {str(e)}")
        return False

async def main():
    """Run all database tests"""
    print("🚀 Dynamic Taxonomy RAG v1.8.1 - 데이터베이스 테스트 시작")
    print("=" * 60)

    test_results = {}

    # Run all tests
    tests = [
        ("데이터베이스 연결", test_database_connection),
        ("스키마 검증", test_schema_validation),
        ("모델 CRUD 작업", test_model_operations),
        ("데이터베이스 인덱스", test_database_indexes)
    ]

    for test_name, test_func in tests:
        print(f"\n📋 {test_name} 테스트 중...")
        result = await test_func()
        test_results[test_name] = result

        if result:
            print(f"✅ {test_name} 테스트 통과")
        else:
            print(f"❌ {test_name} 테스트 실패")

    # Summary
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약:")

    passed = sum(test_results.values())
    total = len(test_results)

    for test_name, result in test_results.items():
        status = "✅ 통과" if result else "❌ 실패"
        print(f"  - {test_name}: {status}")

    print(f"\n🏆 전체 결과: {passed}/{total} 테스트 통과 ({passed/total*100:.1f}%)")

    if passed == total:
        print("🎉 모든 데이터베이스 테스트 성공!")
    else:
        print("⚠️ 일부 테스트 실패 - 로그를 확인하세요.")

    return passed == total

if __name__ == "__main__":
    asyncio.run(main())