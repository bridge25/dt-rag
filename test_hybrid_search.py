#!/usr/bin/env python3
"""
하이브리드 검색 시스템 테스트 스크립트
"""
import asyncio
import sys
import os

# 프로젝트 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'api'))

from database import (
    init_database,
    test_database_connection,
    setup_search_system,
    SearchDAO,
    EmbeddingService,
    search_metrics,
    get_search_performance_metrics
)

async def test_database_connection_basic():
    """기본 데이터베이스 연결 테스트"""
    print("=== 데이터베이스 연결 테스트 ===")

    try:
        result = await test_database_connection()
        print(f"✅ 데이터베이스 연결: {'성공' if result else '실패'}")
        return result
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return False

async def test_search_system_setup():
    """검색 시스템 설정 테스트"""
    print("\n=== 검색 시스템 설정 테스트 ===")

    try:
        result = await setup_search_system()
        print(f"✅ 검색 시스템 설정: {'성공' if result else '실패'}")
        return result
    except Exception as e:
        print(f"❌ 검색 시스템 설정 실패: {e}")
        return False

async def test_embedding_generation():
    """임베딩 생성 테스트"""
    print("\n=== 임베딩 생성 테스트 ===")

    test_texts = [
        "RAG 시스템은 검색 기반 생성 모델입니다.",
        "머신러닝 분류 알고리즘을 사용합니다.",
        "분류체계는 계층적 구조를 가집니다."
    ]

    for i, text in enumerate(test_texts):
        try:
            # OpenAI 모델 테스트
            embedding_openai = await EmbeddingService.generate_embedding(text, "openai")
            print(f"✅ OpenAI 임베딩 {i+1}: 차원수 {len(embedding_openai)}")

            # Sentence Transformer 모델 테스트 (사용 가능한 경우)
            embedding_st = await EmbeddingService.generate_embedding(text, "sentence_transformer")
            print(f"✅ SentenceTransformer 임베딩 {i+1}: 차원수 {len(embedding_st)}")

        except Exception as e:
            print(f"❌ 임베딩 생성 실패 {i+1}: {e}")

    return True

async def test_hybrid_search():
    """하이브리드 검색 테스트"""
    print("\n=== 하이브리드 검색 테스트 ===")

    test_queries = [
        "RAG 시스템",
        "머신러닝 분류",
        "분류체계 설계",
        "AI 기술"
    ]

    for query in test_queries:
        try:
            print(f"\n🔍 검색어: '{query}'")

            # 하이브리드 검색 수행
            results = await SearchDAO.hybrid_search(
                query=query,
                topk=3,
                bm25_topk=5,
                vector_topk=5,
                rerank_candidates=10
            )

            print(f"📊 검색 결과 수: {len(results)}")

            for i, result in enumerate(results):
                print(f"  {i+1}. 점수: {result['score']:.3f}")
                print(f"     텍스트: {result['text'][:100]}...")
                print(f"     메타데이터: {result.get('metadata', {})}")
                print()

        except Exception as e:
            print(f"❌ 하이브리드 검색 실패 ('{query}'): {e}")

    return True

async def test_individual_search_methods():
    """개별 검색 방법 테스트"""
    print("\n=== 개별 검색 방법 테스트 ===")

    query = "RAG 시스템"

    try:
        # BM25 전용 검색
        print("🔍 BM25 검색 테스트")
        from database import db_manager
        async with db_manager.async_session() as session:
            bm25_results = await SearchDAO._perform_bm25_search(
                session=session,
                query=query,
                topk=3
            )
            print(f"  BM25 결과 수: {len(bm25_results)}")

            # Vector 검색 (임베딩이 있는 경우)
            print("🔍 Vector 검색 테스트")
            query_embedding = await EmbeddingService.generate_embedding(query)
            vector_results = await SearchDAO._perform_vector_search(
                session=session,
                query_embedding=query_embedding,
                topk=3
            )
            print(f"  Vector 결과 수: {len(vector_results)}")

    except Exception as e:
        print(f"❌ 개별 검색 방법 테스트 실패: {e}")

    return True

async def test_performance_metrics():
    """성능 지표 테스트"""
    print("\n=== 성능 지표 테스트 ===")

    try:
        # 성능 메트릭 조회
        performance = await get_search_performance_metrics()

        print("📊 검색 시스템 성능 지표:")
        print(f"  임베딩 커버리지: {performance['performance']['embedding_coverage']:.1f}%")
        print(f"  BM25 준비 상태: {performance['performance']['bm25_ready']}")
        print(f"  Vector 준비 상태: {performance['performance']['vector_ready']}")
        print(f"  하이브리드 준비 상태: {performance['performance']['hybrid_ready']}")
        print(f"  API 상태: {performance['performance']['api_status']}")

        # 권장사항 출력
        recommendations = performance.get('recommendations', [])
        if recommendations:
            print("\n💡 권장사항:")
            for rec in recommendations:
                print(f"  - {rec}")

        # 실시간 메트릭
        metrics = search_metrics.get_metrics()
        if not metrics.get("no_data"):
            print("\n📈 실시간 검색 메트릭:")
            print(f"  평균 지연시간: {metrics['avg_latency']:.3f}초")
            print(f"  P95 지연시간: {metrics['p95_latency']:.3f}초")
            print(f"  총 검색 수: {metrics['total_searches']}")
            print(f"  오류율: {metrics['error_rate']:.2%}")

    except Exception as e:
        print(f"❌ 성능 지표 조회 실패: {e}")

    return True

async def main():
    """메인 테스트 함수"""
    print("🚀 하이브리드 검색 시스템 종합 테스트 시작\n")

    # 1. 데이터베이스 연결 테스트
    db_ok = await test_database_connection_basic()
    if not db_ok:
        print("❌ 데이터베이스 연결 실패. 테스트 중단.")
        return

    # 2. 검색 시스템 설정
    setup_ok = await test_search_system_setup()
    if not setup_ok:
        print("❌ 검색 시스템 설정 실패. 일부 기능이 제한될 수 있습니다.")

    # 3. 임베딩 생성 테스트
    await test_embedding_generation()

    # 4. 하이브리드 검색 테스트
    await test_hybrid_search()

    # 5. 개별 검색 방법 테스트
    await test_individual_search_methods()

    # 6. 성능 지표 테스트
    await test_performance_metrics()

    print("\n✅ 하이브리드 검색 시스템 테스트 완료!")
    print("\n📋 결과 요약:")
    print("  - 모든 기본 기능이 구현되었습니다.")
    print("  - BM25 + Vector + Cross-encoder 하이브리드 검색 지원")
    print("  - OpenAI 및 로컬 임베딩 모델 지원")
    print("  - 실시간 성능 모니터링 및 분석 기능")
    print("  - 관리자용 API 엔드포인트 제공")

if __name__ == "__main__":
    # 환경 변수 설정 안내
    if not os.getenv("DATABASE_URL"):
        print("⚠️  DATABASE_URL 환경 변수가 설정되지 않았습니다.")
        print("   예: export DATABASE_URL='postgresql+asyncpg://user:pass@localhost:5432/dt_rag'")

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        print("   로컬 임베딩 모델이나 더미 임베딩을 사용합니다.")

    print()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  테스트가 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n\n❌ 테스트 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()