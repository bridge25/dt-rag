"""
임베딩 캐싱 시스템 테스트
캐시 히트/미스, 성능 측정, 데이터 무결성 검증
"""

import asyncio
import time
import numpy as np
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# pytest 설정
pytestmark = pytest.mark.asyncio

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from apps.search.embedding_cache import EmbeddingCache, CacheStats
from apps.search.embedding_service import OptimizedEmbeddingService, EmbeddingConfig

class TestEmbeddingCache:
    """임베딩 캐시 테스트 클래스"""

    @pytest_asyncio.fixture
    async def cache(self):
        """테스트용 캐시 인스턴스 생성"""
        # Redis 없이 메모리 캐시만 사용
        cache = EmbeddingCache(
            redis_url="redis://nonexistent:6379",  # 연결 실패하도록
            memory_cache_size=100,
            memory_ttl=300,
            enable_compression=False
        )
        # Redis 클라이언트 완전히 비활성화
        cache.redis_client = None
        yield cache
        await cache.close()

    @pytest.fixture
    def sample_embedding(self):
        """테스트용 임베딩 벡터"""
        return np.random.rand(768).astype(np.float32)

    async def test_memory_cache_hit_miss(self, cache, sample_embedding):
        """메모리 캐시 히트/미스 테스트"""
        text = "test text for caching"

        # 캐시 미스 확인
        result = await cache.get_embedding(text)
        assert result is None
        assert cache.stats.misses == 1
        assert cache.stats.hits == 0

        # 캐시에 저장
        success = await cache.set_embedding(text, sample_embedding)
        assert success is True
        assert cache.stats.sets == 1

        # 캐시 히트 확인
        cached_result = await cache.get_embedding(text)
        assert cached_result is not None
        assert np.array_equal(cached_result, sample_embedding)
        assert cache.stats.hits == 1
        assert cache.stats.memory_hits == 1

    async def test_cache_key_generation(self, cache):
        """캐시 키 생성 테스트"""
        text1 = "Test Text"
        text2 = "test text"  # 대소문자 다름
        text3 = "  Test Text  "  # 공백 포함

        key1 = cache._generate_cache_key(text1)
        key2 = cache._generate_cache_key(text2)
        key3 = cache._generate_cache_key(text3)

        # 정규화로 인해 모든 키가 동일해야 함
        assert key1 == key2 == key3
        assert len(key1) == 64  # SHA256 hex length

    async def test_batch_operations(self, cache):
        """배치 작업 테스트"""
        texts = ["text1", "text2", "text3", "text4", "text5"]

        # Mock 임베딩 함수
        async def mock_embedding_func(batch_texts):
            return [np.random.rand(768).astype(np.float32) for _ in batch_texts]

        # 배치 처리
        results = await cache.batch_get_embeddings(
            texts,
            mock_embedding_func,
            batch_size=3
        )

        assert len(results) == len(texts)
        assert all(r is not None for r in results)
        assert cache.stats.sets == len(texts)

        # 두 번째 호출 시 캐시 히트 확인
        cache.stats = CacheStats()  # 통계 초기화
        results2 = await cache.batch_get_embeddings(
            texts,
            mock_embedding_func,
            batch_size=3
        )

        assert len(results2) == len(texts)
        assert cache.stats.hits == len(texts)
        assert cache.stats.sets == 0  # 새로 생성되지 않음

    async def test_embedding_serialization(self, cache, sample_embedding):
        """임베딩 직렬화/역직렬화 테스트"""
        # 직렬화
        serialized = cache._serialize_embedding(sample_embedding)
        assert isinstance(serialized, bytes)
        assert len(serialized) > 0

        # 역직렬화
        deserialized = cache._deserialize_embedding(serialized)
        assert isinstance(deserialized, np.ndarray)
        assert np.array_equal(deserialized, sample_embedding)

    async def test_cache_stats(self, cache, sample_embedding):
        """캐시 통계 테스트"""
        texts = ["test1", "test2", "test3"]

        # 미스 생성
        for text in texts:
            await cache.get_embedding(text)

        # 히트 생성 (일부만 저장 후 재조회)
        for i, text in enumerate(texts[:2]):
            await cache.set_embedding(text, sample_embedding)
            await cache.get_embedding(text)

        stats = cache.get_stats()

        assert stats['total_requests'] == 5  # 3 미스 + 2 히트
        assert stats['misses'] == 3
        assert stats['hits'] == 2
        assert stats['sets'] == 2
        assert stats['hit_rate'] == 0.4  # 2/5
        assert stats['memory_hits'] == 2
        assert stats['redis_available'] is False  # Mock Redis


class TestOptimizedEmbeddingService:
    """최적화된 임베딩 서비스 테스트"""

    @pytest.fixture
    def service_config(self):
        """테스트용 서비스 설정"""
        return EmbeddingConfig(
            provider="local",
            model_name="test-model",
            enable_cache=True,
            batch_size=10
        )

    @pytest_asyncio.fixture
    async def service(self, service_config):
        """테스트용 서비스 인스턴스"""
        with patch('apps.search.embedding_service.get_embedding_cache') as mock_cache:
            mock_cache_instance = AsyncMock()
            mock_cache.return_value = mock_cache_instance

            service = OptimizedEmbeddingService(service_config)
            service.cache = mock_cache_instance
            yield service

    async def test_generate_embedding_with_cache_hit(self, service):
        """캐시 히트 시 임베딩 생성 테스트"""
        text = "test text"
        cached_embedding = np.random.rand(768).astype(np.float32)

        # 캐시 히트 설정
        service.cache.get_embedding.return_value = cached_embedding

        result = await service.generate_embedding(text)

        assert np.array_equal(result, cached_embedding)
        service.cache.get_embedding.assert_called_once_with(text)
        service.cache.set_embedding.assert_not_called()

    async def test_generate_embedding_with_cache_miss(self, service):
        """캐시 미스 시 임베딩 생성 테스트"""
        text = "test text"
        generated_embedding = np.random.rand(768).astype(np.float32)

        # 캐시 미스 설정
        service.cache.get_embedding.return_value = None

        # 로컬 모델 mock
        with patch.object(service, '_generate_local_embedding') as mock_gen:
            mock_gen.return_value = generated_embedding

            result = await service.generate_embedding(text)

            assert np.array_equal(result, generated_embedding)
            service.cache.get_embedding.assert_called_once_with(text)
            service.cache.set_embedding.assert_called_once_with(text, generated_embedding)

    async def test_batch_embeddings_with_mixed_cache(self, service):
        """혼합 캐시 상태에서 배치 임베딩 테스트"""
        texts = ["cached_text", "new_text1", "new_text2"]
        cached_embedding = np.random.rand(768).astype(np.float32)
        new_embeddings = [np.random.rand(768).astype(np.float32) for _ in range(2)]

        # 캐시 설정: 첫 번째는 히트, 나머지는 미스
        async def mock_batch_get_embeddings(texts_list, func, batch_size):
            results = []
            for i, text in enumerate(texts_list):
                if text == "cached_text":
                    results.append(cached_embedding)
                else:
                    # 새로 생성된 것으로 가정
                    idx = i - 1 if i > 0 else 0
                    results.append(new_embeddings[min(idx, len(new_embeddings)-1)])
            return results

        service.cache.batch_get_embeddings.side_effect = mock_batch_get_embeddings

        results = await service.generate_batch_embeddings(texts)

        assert len(results) == len(texts)
        assert all(r is not None for r in results)
        service.cache.batch_get_embeddings.assert_called_once()

    async def test_service_stats(self, service):
        """서비스 통계 테스트"""
        # 캐시 통계 mock
        service.cache.get_stats.return_value = {
            'hits': 10,
            'misses': 5,
            'hit_rate': 0.67
        }

        stats = await service.get_stats()

        assert stats['provider'] == 'local'
        assert stats['cache_enabled'] is True
        assert stats['hits'] == 10
        assert stats['misses'] == 5
        assert stats['hit_rate'] == 0.67


class TestPerformanceImprovements:
    """성능 개선 효과 테스트"""

    async def test_cache_performance_improvement(self):
        """캐시 성능 개선 효과 측정"""
        # 캐시 없는 서비스
        config_no_cache = EmbeddingConfig(
            provider="local",
            enable_cache=False
        )

        # 캐시 있는 서비스
        config_with_cache = EmbeddingConfig(
            provider="local",
            enable_cache=True
        )

        test_texts = ["test text 1", "test text 2", "test text 3"] * 3  # 중복 포함

        # Mock 임베딩 생성 (시간 지연 포함)
        async def slow_embedding_generation(text):
            await asyncio.sleep(0.01)  # 10ms 지연 시뮬레이션
            return np.random.rand(768).astype(np.float32)

        with patch('apps.search.embedding_service.get_embedding_cache') as mock_cache_getter:
            # 캐시 있는 경우
            mock_cache = AsyncMock()
            mock_cache.get_embedding.return_value = None  # 첫 번째는 미스
            mock_cache.set_embedding.return_value = True

            # 두 번째 호출부터는 히트
            call_count = 0
            async def mock_get_embedding(text):
                nonlocal call_count
                call_count += 1
                if call_count > 3:  # 첫 3개 이후는 캐시 히트
                    return np.random.rand(768).astype(np.float32)
                return None

            mock_cache.get_embedding.side_effect = mock_get_embedding
            mock_cache_getter.return_value = mock_cache

            service_with_cache = OptimizedEmbeddingService(config_with_cache)

            with patch.object(service_with_cache, '_generate_local_embedding') as mock_gen:
                mock_gen.side_effect = slow_embedding_generation

                start_time = time.time()
                results = []
                for text in test_texts:
                    result = await service_with_cache.generate_embedding(text)
                    results.append(result)
                cached_time = time.time() - start_time

        # 캐시 없는 경우
        service_no_cache = OptimizedEmbeddingService(config_no_cache)
        with patch.object(service_no_cache, '_generate_local_embedding') as mock_gen:
            mock_gen.side_effect = slow_embedding_generation

            start_time = time.time()
            results = []
            for text in test_texts:
                result = await service_no_cache.generate_embedding(text)
                results.append(result)
            no_cache_time = time.time() - start_time

        # 캐시가 있는 경우가 더 빨라야 함 (중복 처리로 인해)
        improvement_ratio = no_cache_time / cached_time
        print(f"성능 개선 비율: {improvement_ratio:.2f}x")
        assert improvement_ratio > 1.5  # 최소 1.5배 개선


if __name__ == "__main__":
    """직접 실행 시 기본 테스트 수행"""
    async def run_basic_tests():
        print("=== 임베딩 캐시 기본 테스트 ===")

        # 기본 캐시 테스트
        cache = EmbeddingCache(
            redis_url="redis://localhost:6379",
            memory_cache_size=100,
            memory_ttl=60
        )

        try:
            # 테스트 임베딩
            test_embedding = np.random.rand(768).astype(np.float32)
            test_text = "테스트 임베딩 텍스트"

            print("1. 캐시 미스 테스트...")
            result = await cache.get_embedding(test_text)
            print(f"   캐시 미스 결과: {result is None}")

            print("2. 캐시 저장 테스트...")
            success = await cache.set_embedding(test_text, test_embedding)
            print(f"   저장 성공: {success}")

            print("3. 캐시 히트 테스트...")
            cached_result = await cache.get_embedding(test_text)
            hit_success = cached_result is not None and np.array_equal(cached_result, test_embedding)
            print(f"   캐시 히트 성공: {hit_success}")

            print("4. 캐시 통계...")
            stats = cache.get_stats()
            print(f"   총 요청: {stats['total_requests']}")
            print(f"   히트: {stats['hits']}, 미스: {stats['misses']}")
            print(f"   히트율: {stats['hit_rate']:.2%}")

            print("\n=== 임베딩 서비스 테스트 ===")

            # 서비스 테스트
            config = EmbeddingConfig(
                provider="local",
                enable_cache=True,
                batch_size=5
            )

            service = OptimizedEmbeddingService(config)

            print("5. 서비스 상태...")
            service_stats = service.get_stats()
            print(f"   프로바이더: {service_stats['provider']}")
            print(f"   캐시 활성화: {service_stats['cache_enabled']}")

            print("\n✅ 모든 기본 테스트 완료!")

        except Exception as e:
            print(f"❌ 테스트 중 오류 발생: {e}")
        finally:
            await cache.close()

    # asyncio.run(run_basic_tests())
    print("테스트 파일이 생성되었습니다. 'python -m pytest tests/test_embedding_cache.py -v' 로 실행하세요.")