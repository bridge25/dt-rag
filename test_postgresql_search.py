#!/usr/bin/env python3
"""
PostgreSQL + pgvector 환경에서 하이브리드 검색 테스트
"""
import asyncio
import os
import sys
import logging
from typing import List, Dict, Any

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PostgreSQL 환경변수 설정
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/dt_rag_test"

async def test_bm25_search():
    """BM25 검색 테스트"""
    try:
        from apps.search.hybrid_search_engine import HybridSearchEngine
        from apps.api.database import db_manager

        # 데이터베이스 초기화
        await db_manager.init_database()

        # 검색 엔진 생성
        search_engine = HybridSearchEngine()

        # BM25 검색 테스트
        results, metrics = await search_engine.keyword_only_search(
            query="machine learning",
            top_k=5
        )

        logger.info(f"BM25 검색 결과: {len(results)}개 문서")
        logger.info(f"검색 시간: {metrics.total_time:.3f}초")

        for i, result in enumerate(results):
            logger.info(f"  {i+1}. {result.title}: {result.bm25_score:.3f}")

        return True

    except Exception as e:
        logger.error(f"BM25 검색 테스트 실패: {e}")
        return False

async def test_vector_search():
    """Vector 검색 테스트"""
    try:
        from apps.search.hybrid_search_engine import HybridSearchEngine

        search_engine = HybridSearchEngine()

        # Vector 검색 테스트
        results, metrics = await search_engine.vector_only_search(
            query="machine learning",
            top_k=5
        )

        logger.info(f"Vector 검색 결과: {len(results)}개 문서")
        logger.info(f"검색 시간: {metrics.total_time:.3f}초")

        for i, result in enumerate(results):
            logger.info(f"  {i+1}. {result.title}: {result.vector_score:.3f}")

        return True

    except Exception as e:
        logger.error(f"Vector 검색 테스트 실패: {e}")
        return False

async def test_hybrid_search():
    """하이브리드 검색 테스트"""
    try:
        from apps.search.hybrid_search_engine import HybridSearchEngine

        search_engine = HybridSearchEngine()

        # 하이브리드 검색 테스트
        results, metrics = await search_engine.search(
            query="machine learning algorithms",
            top_k=5
        )

        logger.info(f"하이브리드 검색 결과: {len(results)}개 문서")
        logger.info(f"검색 시간: {metrics.total_time:.3f}초")
        logger.info(f"BM25 시간: {metrics.bm25_time:.3f}초")
        logger.info(f"Vector 시간: {metrics.vector_time:.3f}초")
        logger.info(f"Fusion 시간: {metrics.fusion_time:.3f}초")

        for i, result in enumerate(results):
            logger.info(f"  {i+1}. {result.title}: hybrid={result.hybrid_score:.3f}, bm25={result.bm25_score:.3f}, vector={result.vector_score:.3f}")

        return True

    except Exception as e:
        logger.error(f"하이브리드 검색 테스트 실패: {e}")
        return False

async def test_database_connection():
    """데이터베이스 연결 테스트"""
    try:
        from apps.api.database import db_manager

        # 데이터베이스 연결 테스트
        async with db_manager.async_session() as session:
            from sqlalchemy import text

            # PostgreSQL 버전 확인
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"PostgreSQL 버전: {version}")

            # pgvector 확장 확인
            try:
                result = await session.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
                vector_ext = result.scalar()
                if vector_ext:
                    logger.info("pgvector 확장 설치됨")
                else:
                    logger.warning("pgvector 확장 미설치")
            except Exception as e:
                logger.warning(f"pgvector 확장 확인 실패: {e}")

            # 테이블 존재 확인
            tables = ['documents', 'chunks', 'embeddings', 'doc_taxonomy']
            for table in tables:
                try:
                    result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    logger.info(f"{table} 테이블: {count}개 레코드")
                except Exception as e:
                    logger.warning(f"{table} 테이블 확인 실패: {e}")

        return True

    except Exception as e:
        logger.error(f"데이터베이스 연결 테스트 실패: {e}")
        return False

async def main():
    """메인 테스트 실행"""
    logger.info("PostgreSQL + pgvector 하이브리드 검색 테스트 시작")

    tests = [
        ("데이터베이스 연결", test_database_connection),
        ("BM25 검색", test_bm25_search),
        ("Vector 검색", test_vector_search),
        ("하이브리드 검색", test_hybrid_search)
    ]

    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n=== {test_name} 테스트 ===")
        try:
            results[test_name] = await test_func()
        except Exception as e:
            logger.error(f"{test_name} 테스트 중 예외 발생: {e}")
            results[test_name] = False

    # 결과 요약
    logger.info(f"\n=== 테스트 결과 요약 ===")
    passed = 0
    for test_name, result in results.items():
        status = "✅ 성공" if result else "❌ 실패"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1

    logger.info(f"전체 테스트: {passed}/{len(tests)} 성공")
    return passed == len(tests)

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
        sys.exit(1)
    except Exception as e:
        logger.error(f"테스트 실행 중 오류: {e}")
        sys.exit(1)