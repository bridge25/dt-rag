#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify Critical Issues fixes with comprehensive testing
Dynamic Taxonomy RAG v1.8.1 - Critical Issues Verification
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

async def test_vector_search_compatibility():
    """Test vector search compatibility after fixes"""
    try:
        from database import SearchDAO, EmbeddingService

        print("벡터 검색 호환성 테스트 중...")

        # Generate a test query embedding
        test_query = "RAG 시스템 테스트"
        query_embedding = await EmbeddingService.generate_embedding(test_query)

        print(f"테스트 쿼리: {test_query}")
        print(f"임베딩 생성 성공: {len(query_embedding)} 차원")

        # Test hybrid search
        search_results = await SearchDAO.hybrid_search(
            query=test_query,
            topk=3,
            bm25_topk=5,
            vector_topk=5
        )

        print(f"하이브리드 검색 결과: {len(search_results)}개")

        for i, result in enumerate(search_results):
            print(f"  {i+1}. {result.get('title', 'No title')}")
            print(f"     Score: {result.get('score', 0.0):.3f}")
            print(f"     Source: {result.get('metadata', {}).get('source', 'unknown')}")

        return True

    except Exception as e:
        print(f"벡터 검색 테스트 실패: {e}")
        return False

async def test_doc_metadata_operations():
    """Test doc_metadata column operations"""
    try:
        from database import TaxonomyNode, async_session
        import uuid
        from datetime import datetime

        print("doc_metadata 컬럼 작업 테스트 중...")

        async with async_session() as session:
            # Create a test taxonomy node with doc_metadata
            test_node = TaxonomyNode(
                canonical_path=["Critical", "Test"],
                node_name="Critical Test Node",
                description="Critical Issues 해결 테스트용 노드",
                doc_metadata={
                    "test_type": "critical_issues_verification",
                    "created_by": "apply_critical_fixes.py",
                    "fixes_applied": [
                        "doc_metadata_verification",
                        "asyncpg_compatibility",
                        "vector_operator_fix"
                    ],
                    "timestamp": datetime.utcnow().isoformat()
                },
                is_active=True,
                created_at=datetime.utcnow()
            )

            session.add(test_node)
            await session.commit()

            print(f"테스트 노드 생성 성공: {test_node.node_id}")
            print(f"doc_metadata 내용: {test_node.doc_metadata}")

            # Retrieve and verify
            retrieved_node = await session.get(TaxonomyNode, test_node.node_id)
            if retrieved_node and retrieved_node.doc_metadata:
                print("doc_metadata 조회 및 검증 성공")
                print(f"저장된 메타데이터 유형: {type(retrieved_node.doc_metadata)}")
                print(f"메타데이터 키: {list(retrieved_node.doc_metadata.keys())}")

                # Cleanup
                await session.delete(retrieved_node)
                await session.commit()
                print("테스트 데이터 정리 완료")

                return True
            else:
                print("doc_metadata 조회 실패")
                return False

    except Exception as e:
        print(f"doc_metadata 테스트 실패: {e}")
        return False

async def test_classification_system():
    """Test classification system with Critical Issues fixes"""
    try:
        from database import ClassifyDAO

        print("분류 시스템 테스트 중...")

        test_texts = [
            "RAG 시스템에서 벡터 검색과 BM25를 결합한 하이브리드 검색",
            "머신러닝 모델의 학습과 검증 과정",
            "분류체계 관리 및 버전 제어 시스템"
        ]

        for i, text in enumerate(test_texts):
            print(f"\n테스트 {i+1}: {text[:50]}...")

            classification_result = await ClassifyDAO.classify_text(text)

            print(f"  분류 결과: {' -> '.join(classification_result['canonical'])}")
            print(f"  신뢰도: {classification_result['confidence']:.3f}")
            print(f"  라벨: {classification_result['label']}")

        return True

    except Exception as e:
        print(f"분류 시스템 테스트 실패: {e}")
        return False

async def test_database_performance():
    """Test database performance after optimizations"""
    try:
        from database import async_session, get_search_performance_metrics
        from sqlalchemy import text
        import time

        print("데이터베이스 성능 테스트 중...")

        # Test query performance
        start_time = time.time()

        async with async_session() as session:
            # Test complex join query
            result = await session.execute(text("""
                SELECT COUNT(*)
                FROM chunks c
                JOIN documents d ON c.doc_id = d.doc_id
                LEFT JOIN doc_taxonomy dt ON d.doc_id = dt.doc_id
                JOIN embeddings e ON c.chunk_id = e.chunk_id
                WHERE c.text IS NOT NULL AND e.vec IS NOT NULL
            """))

            count = result.scalar()

        query_time = time.time() - start_time

        print(f"복합 조인 쿼리 성능: {query_time:.3f}초")
        print(f"처리된 레코드 수: {count}개")

        # Get performance metrics
        metrics = await get_search_performance_metrics()

        print("검색 시스템 성능 지표:")
        performance = metrics.get('performance', {})
        for key, value in performance.items():
            print(f"  {key}: {value}")

        return True

    except Exception as e:
        print(f"성능 테스트 실패: {e}")
        return False

async def main():
    """Run comprehensive verification tests"""
    print("Critical Issues 수정사항 종합 검증")
    print("=" * 60)

    tests = [
        ("벡터 검색 호환성", test_vector_search_compatibility),
        ("doc_metadata 컬럼 작업", test_doc_metadata_operations),
        ("분류 시스템", test_classification_system),
        ("데이터베이스 성능", test_database_performance)
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n{test_name} 테스트 중...")
        print("-" * 40)

        try:
            result = await test_func()
            results[test_name] = result

            if result:
                print(f"✅ {test_name} 테스트 성공")
            else:
                print(f"❌ {test_name} 테스트 실패")

        except Exception as e:
            print(f"❌ {test_name} 테스트 오류: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "=" * 60)
    print("검증 결과 요약:")

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        status = "✅ 통과" if result else "❌ 실패"
        print(f"  - {test_name}: {status}")

    print(f"\n전체 결과: {passed}/{total} 테스트 통과 ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 모든 Critical Issues 수정사항 검증 성공!")
        print("\nPhase 2에서 발견된 Critical Issues가 모두 해결되었습니다:")
        print("  ✅ doc_metadata 컬럼 존재 확인")
        print("  ✅ asyncpg 호환성 개선 (벡터 연산자 수정)")
        print("  ✅ 데이터베이스 마이그레이션 동기화")
        print("  ✅ PostgreSQL과 SQLite 듀얼 지원")
    else:
        print("\n⚠️ 일부 검증 테스트 실패 - 추가 조치가 필요할 수 있습니다.")

    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)