"""
Redis 연결 문제 수정 테스트
FakeRedis 폴백 기능 검증
"""

import asyncio
import numpy as np
import sys
import os

# 프로젝트 루트 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps'))

from search.embedding_cache import EmbeddingCache

async def test_redis_fallback():
    print("Redis 폴백 기능 테스트 시작...")

    # 실제 Redis URL로 시도 (실패할 가능성 높음)
    cache = EmbeddingCache(
        redis_url="redis://localhost:6379",
        memory_cache_size=100,
        memory_ttl=300,
        enable_compression=False
    )

    try:
        # 테스트 임베딩
        test_embedding = np.random.rand(768).astype(np.float32)
        test_text = "Redis fallback test text"

        print("1. 캐시 미스 테스트...")
        result = await cache.get_embedding(test_text)
        print(f"   미스 결과: {result is None}")

        print("2. 캐시 저장 테스트...")
        success = await cache.set_embedding(test_text, test_embedding)
        print(f"   저장 성공: {success}")

        if success:
            print("3. 캐시 히트 테스트...")
            cached_result = await cache.get_embedding(test_text)
            hit_success = cached_result is not None and np.array_equal(cached_result, test_embedding)
            print(f"   히트 성공: {hit_success}")

        print("4. 캐시 통계...")
        stats = cache.get_stats()
        print(f"   총 요청: {stats['total_requests']}")
        print(f"   히트: {stats['hits']}, 미스: {stats['misses']}")
        print(f"   Redis 사용 가능: {stats['redis_available']}")

        print("5. Redis 연결 상태...")
        if cache.redis_client:
            print("   Redis 클라이언트: 활성화됨")
            print(f"   클라이언트 타입: {type(cache.redis_client)}")
        else:
            print("   Redis 클라이언트: 비활성화됨")

        print("\nRedis 폴백 테스트 완료!")

    except Exception as e:
        print(f"테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await cache.close()

if __name__ == "__main__":
    asyncio.run(test_redis_fallback())