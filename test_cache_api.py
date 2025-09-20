#!/usr/bin/env python3
"""
캐시 시스템 통합 테스트
Redis/FakeRedis 설정과 임베딩 캐시 기능을 직접 테스트
"""

import asyncio
import time
import numpy as np
from apps.search.embedding_cache import EmbeddingCache, initialize_embedding_cache
from apps.search.embedding_service import OptimizedEmbeddingService, EmbeddingConfig


async def test_cache_functionality():
    """캐시 기능 직접 테스트"""
    print("[CACHE TEST] 임베딩 캐시 시스템 테스트 시작...")

    # 1. 캐시 초기화 테스트
    cache = await initialize_embedding_cache()
    print(f"[OK] 캐시 초기화 완료 - Redis 사용 가능: {cache.redis_client is not None}")

    # 2. 기본 캐시 작동 테스트
    test_text = "Machine learning is a subset of artificial intelligence"
    test_embedding = np.random.rand(1536).astype(np.float32)

    # 캐시에 저장
    await cache.set_embedding(test_text, test_embedding)
    print("[OK] 임베딩 캐시 저장 완료")

    # 캐시에서 조회
    cached_embedding = await cache.get_embedding(test_text)
    assert cached_embedding is not None, "캐시에서 임베딩을 가져올 수 없음"
    assert np.allclose(test_embedding, cached_embedding), "캐시된 임베딩이 일치하지 않음"
    print("[OK] 임베딩 캐시 조회 성공")

    # 3. 배치 작업 테스트
    test_texts = [
        "Natural language processing",
        "Computer vision applications",
        "Deep learning networks"
    ]
    test_embeddings = [np.random.rand(1536).astype(np.float32) for _ in test_texts]

    # 개별적으로 저장
    for text, embedding in zip(test_texts, test_embeddings):
        await cache.set_embedding(text, embedding)

    # 개별로 조회 확인
    cached_batch = []
    for text in test_texts:
        cached = await cache.get_embedding(text)
        cached_batch.append(cached)
    assert len(cached_batch) == len(test_texts), "배치 조회 결과 수가 일치하지 않음"
    assert all(c is not None for c in cached_batch), "일부 캐시 결과가 None임"
    print("[OK] 배치 캐시 작업 성공")

    # 4. 통계 정보 테스트
    stats = cache.get_stats()
    print(f"[STATS] 캐시 통계: {stats}")

    # 5. 임베딩 서비스 통합 테스트
    config = EmbeddingConfig(
        provider="local",
        enable_cache=True,
        cache_ttl=3600
    )

    service = OptimizedEmbeddingService(config)
    print("[OK] 임베딩 서비스 초기화 완료")

    # 성능 테스트 - 캐시 히트 vs 미스
    test_query = "What is artificial intelligence?"

    # 첫 번째 요청 (캐시 미스)
    start_time = time.time()
    embedding1 = await service.generate_embedding(test_query)
    miss_time = time.time() - start_time

    # 두 번째 요청 (캐시 히트)
    start_time = time.time()
    embedding2 = await service.generate_embedding(test_query)
    hit_time = time.time() - start_time

    assert embedding1 is not None, "첫 번째 임베딩 생성 실패"
    assert embedding2 is not None, "두 번째 임베딩 생성 실패"

    if hit_time > 0:
        speedup = miss_time / hit_time
        print(f"[PERF] 캐시 성능 향상: {speedup:.1f}배 (미스: {miss_time:.3f}s, 히트: {hit_time:.3f}s)")
    else:
        print("[PERF] 캐시 히트 응답 시간이 측정 불가능할 정도로 빠름")

    # 6. 서비스 통계 테스트
    service_stats = await service.get_stats()
    print(f"[STATS] 서비스 통계: {service_stats}")

    print("[SUCCESS] 모든 캐시 테스트 완료!")
    return True


async def test_performance_improvement():
    """성능 개선 효과 측정"""
    print("\n[STATS] 성능 개선 효과 측정...")

    # 캐시 없는 서비스
    config_no_cache = EmbeddingConfig(
        provider="local",
        enable_cache=False
    )
    service_no_cache = OptimizedEmbeddingService(config_no_cache)

    # 캐시 있는 서비스
    config_with_cache = EmbeddingConfig(
        provider="local",
        enable_cache=True,
        cache_ttl=3600
    )
    service_with_cache = OptimizedEmbeddingService(config_with_cache)

    test_queries = [
        "Machine learning algorithms",
        "Deep neural networks",
        "Natural language processing",
        "Computer vision tasks",
        "Reinforcement learning"
    ]

    # 캐시 없이 처리
    start_time = time.time()
    for query in test_queries:
        await service_no_cache.generate_embedding(query)
    no_cache_time = time.time() - start_time

    # 캐시로 워밍업
    for query in test_queries:
        await service_with_cache.generate_embedding(query)

    # 캐시로 재처리
    start_time = time.time()
    for query in test_queries:
        await service_with_cache.generate_embedding(query)
    with_cache_time = time.time() - start_time

    if with_cache_time > 0:
        improvement = (no_cache_time - with_cache_time) / no_cache_time * 100
        speedup = no_cache_time / with_cache_time
        print(f"[PERF] 성능 개선 효과:")
        print(f"   - 캐시 없음: {no_cache_time:.3f}s")
        print(f"   - 캐시 있음: {with_cache_time:.3f}s")
        print(f"   - 개선률: {improvement:.1f}%")
        print(f"   - 속도 향상: {speedup:.1f}배")

        if improvement >= 70:
            print("[TARGET] 목표 성능 개선 70% 달성!")
        else:
            print(f"[WARNING] 목표 성능 개선 70% 미달성 (현재: {improvement:.1f}%)")
    else:
        print("[PERF] 캐시 성능이 측정 불가능할 정도로 빠름")


if __name__ == "__main__":
    asyncio.run(test_cache_functionality())
    asyncio.run(test_performance_improvement())