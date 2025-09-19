#!/usr/bin/env python3
"""
최적화된 하이브리드 검색 성능 벤치마크
임베딩 캐시 및 연결 풀 최적화 적용
"""

import asyncio
import time
import sys
import os
import hashlib
import json
from typing import Dict, List, Any
import httpx

# 프로젝트 루트 경로 추가
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps', 'api'))

# 임베딩 캐시 (메모리 기반)
EMBEDDING_CACHE: Dict[str, List[float]] = {}
HTTP_CLIENT = None

class OptimizedEmbeddingService:
    """최적화된 임베딩 서비스"""

    @staticmethod
    async def get_http_client():
        """HTTP 클라이언트 싱글톤"""
        global HTTP_CLIENT
        if HTTP_CLIENT is None:
            HTTP_CLIENT = httpx.AsyncClient(
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
                timeout=httpx.Timeout(30.0)
            )
        return HTTP_CLIENT

    @staticmethod
    def get_cache_key(text: str) -> str:
        """캐시 키 생성"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    @staticmethod
    async def generate_embedding_cached(text: str) -> List[float]:
        """캐시된 임베딩 생성"""
        cache_key = OptimizedEmbeddingService.get_cache_key(text)

        # 캐시에서 확인
        if cache_key in EMBEDDING_CACHE:
            print(f"Cache HIT for text: {text[:50]}...")
            return EMBEDDING_CACHE[cache_key]

        print(f"Cache MISS for text: {text[:50]}...")

        # OpenAI API 호출
        try:
            client = await OptimizedEmbeddingService.get_http_client()

            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                    "Content-Type": "application/json"
                },
                json={
                    "input": text,
                    "model": "text-embedding-ada-002"
                }
            )

            if response.status_code == 200:
                data = response.json()
                embedding = data["data"][0]["embedding"]

                # 캐시에 저장
                EMBEDDING_CACHE[cache_key] = embedding

                return embedding
            else:
                print(f"OpenAI API error: {response.status_code} - {response.text}")
                return [0.0] * 1536  # 기본 임베딩

        except Exception as e:
            print(f"Embedding generation error: {e}")
            return [0.0] * 1536  # 기본 임베딩

    @staticmethod
    async def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
        """배치 임베딩 생성"""
        if len(texts) <= 1:
            if texts:
                return [await OptimizedEmbeddingService.generate_embedding_cached(texts[0])]
            return []

        # 개별 생성 (OpenAI 배치 API는 별도 구현 필요)
        embeddings = []
        for text in texts:
            embedding = await OptimizedEmbeddingService.generate_embedding_cached(text)
            embeddings.append(embedding)

        return embeddings

class OptimizedSearchDAO:
    """최적화된 검색 DAO"""

    @staticmethod
    async def optimized_hybrid_search(
        query: str,
        filters: Dict = None,
        topk: int = 5,
        bm25_topk: int = 12,
        vector_topk: int = 12,
        rerank_candidates: int = 50
    ) -> List[Dict[str, Any]]:
        """최적화된 하이브리드 검색"""
        from database import db_manager, SearchDAO

        start_time = time.time()

        async with db_manager.async_session() as session:
            try:
                # 1. 쿼리 임베딩 생성 (캐시 사용)
                embedding_start = time.time()
                query_embedding = await OptimizedEmbeddingService.generate_embedding_cached(query)
                embedding_time = time.time() - embedding_start

                # 2. BM25 검색 (기존 로직)
                bm25_start = time.time()
                bm25_results = await SearchDAO._perform_bm25_search(
                    session, query, bm25_topk, filters
                )
                bm25_time = time.time() - bm25_start

                # 3. Vector 검색 (기존 로직)
                vector_start = time.time()
                vector_results = await SearchDAO._perform_vector_search(
                    session, query_embedding, vector_topk, filters
                )
                vector_time = time.time() - vector_start

                # 4. 결과 합성 (간단한 스코어 조합)
                combine_start = time.time()
                combined_results = OptimizedSearchDAO._combine_results_optimized(
                    bm25_results, vector_results, rerank_candidates
                )
                combine_time = time.time() - combine_start

                # 성능 정보 추가
                total_time = time.time() - start_time

                # 결과에 성능 메트릭 추가
                for result in combined_results[:topk]:
                    result['_performance'] = {
                        'total_time': total_time,
                        'embedding_time': embedding_time,
                        'bm25_time': bm25_time,
                        'vector_time': vector_time,
                        'combine_time': combine_time,
                        'cache_hit': embedding_time < 0.1
                    }

                return combined_results[:topk]

            except Exception as e:
                print(f"Optimized hybrid search error: {e}")
                # 폴백: 기존 검색 사용
                return await SearchDAO.hybrid_search(query, filters, topk, bm25_topk, vector_topk, rerank_candidates)

    @staticmethod
    def _combine_results_optimized(
        bm25_results: List[Dict],
        vector_results: List[Dict],
        topk: int
    ) -> List[Dict[str, Any]]:
        """최적화된 결과 조합 (간단한 가중평균)"""

        # 결과를 chunk_id로 인덱싱
        all_results = {}

        # BM25 결과 추가
        for result in bm25_results:
            chunk_id = result.get('chunk_id')
            if chunk_id:
                all_results[chunk_id] = result.copy()
                all_results[chunk_id]['bm25_score'] = result.get('score', 0)
                all_results[chunk_id]['vector_score'] = 0

        # Vector 결과 추가/업데이트
        for result in vector_results:
            chunk_id = result.get('chunk_id')
            if chunk_id:
                if chunk_id in all_results:
                    all_results[chunk_id]['vector_score'] = result.get('score', 0)
                else:
                    all_results[chunk_id] = result.copy()
                    all_results[chunk_id]['bm25_score'] = 0
                    all_results[chunk_id]['vector_score'] = result.get('score', 0)

        # 하이브리드 점수 계산 (가중평균)
        for chunk_id, result in all_results.items():
            bm25_score = result.get('bm25_score', 0)
            vector_score = result.get('vector_score', 0)

            # 정규화 및 가중 평균
            hybrid_score = 0.3 * bm25_score + 0.7 * vector_score
            result['score'] = hybrid_score

        # 점수순 정렬
        sorted_results = sorted(
            all_results.values(),
            key=lambda x: x.get('score', 0),
            reverse=True
        )

        return sorted_results[:topk]

async def benchmark_optimized_search():
    """최적화된 검색 벤치마크"""
    print("=== 최적화된 하이브리드 검색 벤치마크 ===")

    test_queries = [
        "machine learning algorithms",
        "vector similarity search",
        "BM25 ranking function",
        "hybrid search systems",
        "neural network deep learning",
        "natural language processing",
        "information retrieval",
        "embedding models AI",
        "cross encoder reranking",
        "document classification"
    ]

    # 첫 번째 라운드: 캐시 MISS
    print("\n1. 첫 번째 라운드 (캐시 MISS)")
    first_round_times = []

    for i, query in enumerate(test_queries):
        start_time = time.time()
        results = await OptimizedSearchDAO.optimized_hybrid_search(
            query=query,
            topk=3
        )
        latency = time.time() - start_time
        first_round_times.append(latency)

        print(f"  Query {i+1}: {len(results)} results, {latency*1000:.1f}ms")

        # 성능 정보 출력
        if results and '_performance' in results[0]:
            perf = results[0]['_performance']
            print(f"    Embedding: {perf['embedding_time']*1000:.1f}ms, "
                  f"BM25: {perf['bm25_time']*1000:.1f}ms, "
                  f"Vector: {perf['vector_time']*1000:.1f}ms")

    # 두 번째 라운드: 캐시 HIT
    print("\n2. 두 번째 라운드 (캐시 HIT)")
    second_round_times = []

    for i, query in enumerate(test_queries):
        start_time = time.time()
        results = await OptimizedSearchDAO.optimized_hybrid_search(
            query=query,
            topk=3
        )
        latency = time.time() - start_time
        second_round_times.append(latency)

        print(f"  Query {i+1}: {len(results)} results, {latency*1000:.1f}ms")

        # 성능 정보 출력
        if results and '_performance' in results[0]:
            perf = results[0]['_performance']
            print(f"    Embedding: {perf['embedding_time']*1000:.1f}ms, "
                  f"Cache Hit: {perf['cache_hit']}")

    # 성능 비교
    print(f"\n=== 성능 비교 ===")
    avg_first = sum(first_round_times) / len(first_round_times) * 1000
    avg_second = sum(second_round_times) / len(second_round_times) * 1000
    improvement = (avg_first - avg_second) / avg_first * 100

    print(f"첫 번째 라운드 평균: {avg_first:.1f}ms")
    print(f"두 번째 라운드 평균: {avg_second:.1f}ms")
    print(f"성능 향상: {improvement:.1f}%")

    # 캐시 통계
    print(f"\n=== 캐시 통계 ===")
    print(f"캐시된 임베딩 수: {len(EMBEDDING_CACHE)}")

    return {
        'first_round_avg': avg_first,
        'second_round_avg': avg_second,
        'improvement_percent': improvement,
        'cache_size': len(EMBEDDING_CACHE)
    }

async def benchmark_concurrent_optimized():
    """최적화된 동시 검색 벤치마크"""
    print("\n=== 최적화된 동시 검색 벤치마크 ===")

    concurrent_queries = [
        "AI technology trends",
        "machine learning models",
        "data processing algorithms",
        "software optimization",
        "neural network architecture",
        "search engine design",
        "vector databases",
        "text embedding methods"
    ]

    print(f"실행: {len(concurrent_queries)}개 동시 쿼리")

    start_time = time.time()

    # 동시 실행
    tasks = []
    for query in concurrent_queries:
        task = OptimizedSearchDAO.optimized_hybrid_search(
            query=query,
            topk=3
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)
    total_time = time.time() - start_time

    successful_results = [r for r in results if not isinstance(r, Exception)]
    failed_results = [r for r in results if isinstance(r, Exception)]

    print(f"총 실행시간: {total_time*1000:.1f}ms")
    print(f"성공: {len(successful_results)}/{len(concurrent_queries)}")
    print(f"실패: {len(failed_results)}")

    if successful_results:
        avg_results = sum(len(r) for r in successful_results) / len(successful_results)
        print(f"평균 결과 수: {avg_results:.1f}")

        # 동시 처리 효율성
        sequential_estimate = len(concurrent_queries) * 100  # 100ms per query 추정 (캐시 적용)
        efficiency = max(0, (sequential_estimate - total_time*1000) / sequential_estimate * 100)
        print(f"동시 처리 효율성: {efficiency:.1f}%")

        # 캐시 히트율 계산
        cache_hits = 0
        total_searches = 0
        for result_list in successful_results:
            for result in result_list:
                if '_performance' in result and result['_performance'].get('cache_hit'):
                    cache_hits += 1
                total_searches += 1

        hit_rate = (cache_hits / total_searches * 100) if total_searches > 0 else 0
        print(f"캐시 히트율: {hit_rate:.1f}%")

    return {
        'total_time': total_time * 1000,
        'success_rate': len(successful_results) / len(concurrent_queries) * 100,
        'efficiency': efficiency if successful_results else 0
    }

async def cleanup():
    """리소스 정리"""
    global HTTP_CLIENT
    if HTTP_CLIENT:
        await HTTP_CLIENT.aclose()
        HTTP_CLIENT = None

async def main():
    """메인 실행 함수"""
    print("Dynamic Taxonomy RAG v1.8.1 - 최적화된 검색 성능 벤치마크")
    print("="*70)

    try:
        # 최적화된 검색 벤치마크
        search_results = await benchmark_optimized_search()

        # 최적화된 동시 검색 벤치마크
        concurrent_results = await benchmark_concurrent_optimized()

        # 최종 요약
        print(f"\n{'='*70}")
        print("최적화 성능 요약")
        print(f"{'='*70}")

        print(f"단일 검색 성능:")
        print(f"  캐시 미적용시: {search_results['first_round_avg']:.1f}ms")
        print(f"  캐시 적용시: {search_results['second_round_avg']:.1f}ms")
        print(f"  성능 향상: {search_results['improvement_percent']:.1f}%")

        print(f"\n동시 검색 성능:")
        print(f"  총 실행시간: {concurrent_results['total_time']:.1f}ms")
        print(f"  성공률: {concurrent_results['success_rate']:.1f}%")
        print(f"  처리 효율성: {concurrent_results['efficiency']:.1f}%")

        # 목표 달성도 평가
        print(f"\n목표 달성도:")
        if search_results['second_round_avg'] < 100:
            print("✅ 캐시 적용시 지연시간 목표 달성")
        else:
            print("❌ 지연시간 목표 미달성")

        if concurrent_results['success_rate'] >= 95:
            print("✅ 안정성 목표 달성")
        else:
            print("❌ 안정성 목표 미달성")

        # 추가 최적화 권장사항
        print(f"\n추가 최적화 권장:")
        if search_results['improvement_percent'] > 50:
            print("✅ 캐시 최적화 효과 우수")
        else:
            print("🟡 추가 캐시 최적화 필요")

        print("🔧 다음 단계: BM25 FTS 인덱스 구현")
        print("🔧 다음 단계: 비동기 파이프라인 구현")
        print("🔧 다음 단계: 로컬 임베딩 모델 고려")

    finally:
        await cleanup()

if __name__ == "__main__":
    asyncio.run(main())