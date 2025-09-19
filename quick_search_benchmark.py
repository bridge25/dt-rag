#!/usr/bin/env python3
"""
빠른 하이브리드 검색 성능 테스트
데이터베이스 연결 및 기본 검색 기능 검증
"""

import asyncio
import time
import sys
import os

# 프로젝트 루트 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps', 'api'))

async def test_database_connection():
    """Database connection test"""
    print("=== Database Connection Test ===")

    try:
        from database import db_manager, SearchDAO

        # Async session creation test
        async with db_manager.async_session() as session:
            print("OK Database session created successfully")

            # Check table existence
            chunk_count = await SearchDAO._get_chunk_count(session)
            print(f"OK Document chunks found: {chunk_count}")

            # 간단한 검색 테스트
            if chunk_count > 0:
                print("\n간단한 검색 테스트 실행 중...")

                # BM25 검색 테스트
                start_time = time.time()
                bm25_results = await SearchDAO._perform_bm25_search(
                    session=session,
                    query="AI machine learning",
                    topk=5,
                    filters=None
                )
                bm25_time = time.time() - start_time
                print(f"✓ BM25 검색: {len(bm25_results)}개 결과, {bm25_time*1000:.1f}ms")

                # 하이브리드 검색 테스트
                start_time = time.time()
                hybrid_results = await SearchDAO.hybrid_search(
                    query="AI machine learning",
                    filters=None,
                    topk=5,
                    bm25_topk=10,
                    vector_topk=10,
                    rerank_candidates=20
                )
                hybrid_time = time.time() - start_time
                print(f"✓ 하이브리드 검색: {len(hybrid_results)}개 결과, {hybrid_time*1000:.1f}ms")

                # 성능 목표 확인
                print(f"\n성능 평가:")
                if bm25_time * 1000 < 50:
                    print("✓ BM25 검색 속도 우수 (< 50ms)")
                elif bm25_time * 1000 < 100:
                    print("○ BM25 검색 속도 양호 (< 100ms)")
                else:
                    print("✗ BM25 검색 속도 개선 필요 (> 100ms)")

                if hybrid_time * 1000 < 200:
                    print("✓ 하이브리드 검색 속도 우수 (< 200ms)")
                elif hybrid_time * 1000 < 500:
                    print("○ 하이브리드 검색 속도 양호 (< 500ms)")
                else:
                    print("✗ 하이브리드 검색 속도 개선 필요 (> 500ms)")
            else:
                print("⚠ 데이터베이스에 문서가 없습니다.")

    except ImportError as e:
        print(f"✗ 데이터베이스 모듈 import 실패: {e}")
        print("앱 경로를 확인하거나 의존성을 설치해주세요.")
        return False
    except Exception as e:
        print(f"✗ 데이터베이스 연결 실패: {e}")
        return False

    return True

async def test_search_scenarios():
    """다양한 검색 시나리오 테스트"""
    print("\n=== 검색 시나리오 테스트 ===")

    try:
        from database import SearchDAO

        test_queries = [
            ("simple", "AI"),
            ("medium", "machine learning algorithms"),
            ("complex", "how to implement vector similarity search"),
            ("korean", "인공지능 머신러닝"),
            ("technical", "BM25 algorithm implementation")
        ]

        results = []

        for scenario, query in test_queries:
            print(f"\n[{scenario.upper()}] 쿼리: '{query}'")

            start_time = time.time()
            search_results = await SearchDAO.hybrid_search(
                query=query,
                filters=None,
                topk=5,
                bm25_topk=12,
                vector_topk=12,
                rerank_candidates=20
            )
            latency = time.time() - start_time

            print(f"  결과: {len(search_results)}개")
            print(f"  지연시간: {latency*1000:.1f}ms")

            if search_results:
                avg_score = sum(r.get('score', 0) for r in search_results) / len(search_results)
                print(f"  평균 점수: {avg_score:.3f}")

                # 상위 결과 미리보기
                top_result = search_results[0]
                text_preview = top_result.get('text', '')[:100] + '...' if top_result.get('text') else 'N/A'
                print(f"  상위 결과: {text_preview}")

            results.append({
                'scenario': scenario,
                'query': query,
                'count': len(search_results),
                'latency_ms': latency * 1000,
                'avg_score': avg_score if search_results else 0
            })

        # 전체 성능 요약
        print(f"\n=== 성능 요약 ===")
        total_latency = sum(r['latency_ms'] for r in results)
        avg_latency = total_latency / len(results)
        max_latency = max(r['latency_ms'] for r in results)

        print(f"평균 응답시간: {avg_latency:.1f}ms")
        print(f"최대 응답시간: {max_latency:.1f}ms")
        print(f"처리량 추정: {1000/avg_latency:.1f} req/sec")

        # 성능 목표 달성도
        if avg_latency < 100:
            print("✓ 평균 응답시간 목표 달성")
        else:
            print("✗ 평균 응답시간 목표 미달성")

        if max_latency < 200:
            print("✓ 최대 응답시간 목표 달성")
        else:
            print("✗ 최대 응답시간 목표 미달성")

        return results

    except Exception as e:
        print(f"✗ 검색 시나리오 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return []

async def test_concurrent_performance():
    """간단한 동시 검색 성능 테스트"""
    print("\n=== 동시 검색 성능 테스트 ===")

    try:
        from database import SearchDAO

        # 5개 동시 쿼리 실행
        queries = [
            "AI machine learning",
            "vector search",
            "document classification",
            "embedding model",
            "hybrid ranking"
        ]

        print(f"{len(queries)}개 쿼리 동시 실행...")

        start_time = time.time()

        # asyncio.gather로 동시 실행
        tasks = []
        for query in queries:
            task = SearchDAO.hybrid_search(
                query=query,
                filters=None,
                topk=3,
                bm25_topk=8,
                vector_topk=8,
                rerank_candidates=15
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        total_time = time.time() - start_time

        successful_results = [r for r in results if not isinstance(r, Exception)]
        error_results = [r for r in results if isinstance(r, Exception)]

        print(f"총 실행시간: {total_time*1000:.1f}ms")
        print(f"성공한 검색: {len(successful_results)}/{len(queries)}")
        print(f"실패한 검색: {len(error_results)}")

        if successful_results:
            avg_result_count = sum(len(r) for r in successful_results) / len(successful_results)
            print(f"평균 결과 수: {avg_result_count:.1f}개")

            # 동시 처리 효율성 계산
            sequential_estimate = len(queries) * 200  # 200ms per query 추정
            efficiency = (sequential_estimate - total_time*1000) / sequential_estimate * 100
            print(f"동시 처리 효율성: {efficiency:.1f}%")

        if error_results:
            print(f"오류 상세:")
            for i, error in enumerate(error_results):
                print(f"  오류 {i+1}: {error}")

        return len(successful_results), total_time

    except Exception as e:
        print(f"✗ 동시 검색 테스트 실패: {e}")
        return 0, 0

async def main():
    """메인 실행 함수"""
    print("Dynamic Taxonomy RAG v1.8.1 빠른 검색 성능 테스트")
    print("="*60)

    # 1. 데이터베이스 연결 테스트
    if not await test_database_connection():
        print("데이터베이스 연결에 실패했습니다.")
        return

    # 2. 검색 시나리오 테스트
    scenario_results = await test_search_scenarios()

    if scenario_results:
        # 3. 동시 검색 테스트
        concurrent_success, concurrent_time = await test_concurrent_performance()

        # 최종 요약
        print(f"\n{'='*60}")
        print("최종 성능 요약")
        print(f"{'='*60}")

        avg_latency = sum(r['latency_ms'] for r in scenario_results) / len(scenario_results)
        print(f"단일 검색 평균 지연시간: {avg_latency:.1f}ms")
        print(f"동시 검색 성공률: {concurrent_success}/5")
        print(f"동시 검색 총 시간: {concurrent_time*1000:.1f}ms")

        # 성능 등급 평가
        grade = "A"
        if avg_latency > 100:
            grade = "B"
        if avg_latency > 200:
            grade = "C"
        if concurrent_success < 5:
            grade = max("C", grade)

        print(f"전체 성능 등급: {grade}")

        if grade == "A":
            print("✓ 우수한 성능 - 프로덕션 준비 완료")
        elif grade == "B":
            print("○ 양호한 성능 - 일부 최적화 권장")
        else:
            print("✗ 성능 개선 필요 - 최적화 작업 필요")

if __name__ == "__main__":
    asyncio.run(main())