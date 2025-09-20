"""
임베딩 캐싱 시스템 - 70% 성능 향상을 위한 다층 캐싱
Redis + 메모리 캐시를 활용한 고성능 임베딩 저장/조회
"""

import asyncio
import hashlib
import json
import logging
import time
import base64
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass
import numpy as np

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available, using memory-only cache")

try:
    import fakeredis.aioredis
    FAKEREDIS_AVAILABLE = True
except ImportError:
    FAKEREDIS_AVAILABLE = False

from cachetools import TTLCache
import threading

logger = logging.getLogger(__name__)

@dataclass
class CacheStats:
    """캐시 통계"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    memory_hits: int = 0
    redis_hits: int = 0
    total_requests: int = 0

    @property
    def hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests

    @property
    def memory_hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.memory_hits / self.total_requests


class EmbeddingCache:
    """고성능 임베딩 캐싱 시스템"""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        memory_cache_size: int = 10000,
        memory_ttl: int = 3600,  # 1시간
        redis_ttl: int = 86400,  # 24시간
        enable_compression: bool = True
    ):
        """
        Args:
            redis_url: Redis 연결 URL
            memory_cache_size: 메모리 캐시 최대 크기
            memory_ttl: 메모리 캐시 TTL (초)
            redis_ttl: Redis 캐시 TTL (초)
            enable_compression: 압축 활성화 여부
        """
        self.memory_cache = TTLCache(maxsize=memory_cache_size, ttl=memory_ttl)
        self.memory_lock = threading.RLock()
        self.redis_client = None
        self.redis_ttl = redis_ttl
        self.enable_compression = enable_compression
        self.stats = CacheStats()

        # Redis 초기화
        if REDIS_AVAILABLE:
            try:
                self.redis_client = aioredis.from_url(redis_url, decode_responses=False)
                # Redis 연결 테스트
                # 실제 연결 테스트는 비동기로 해야 하므로 여기서는 클라이언트만 생성
                logger.info("Redis cache initialized")
            except Exception as e:
                logger.warning(f"Redis initialization failed: {e}")
                # FakeRedis로 폴백
                if FAKEREDIS_AVAILABLE:
                    try:
                        self.redis_client = fakeredis.aioredis.FakeRedis(decode_responses=False)
                        logger.info("Using FakeRedis as fallback")
                    except Exception as e2:
                        logger.warning(f"FakeRedis initialization failed: {e2}")
                        self.redis_client = None
                else:
                    self.redis_client = None
        elif FAKEREDIS_AVAILABLE:
            try:
                self.redis_client = fakeredis.aioredis.FakeRedis(decode_responses=False)
                logger.info("Using FakeRedis (no real Redis available)")
            except Exception as e:
                logger.warning(f"FakeRedis initialization failed: {e}")
                self.redis_client = None
        else:
            logger.info("No Redis available, using memory cache only")

    async def get_embedding(self, text: str) -> Optional[np.ndarray]:
        """임베딩 조회 (메모리 → Redis → None 순서)"""
        self.stats.total_requests += 1
        cache_key = self._generate_cache_key(text)

        # L1: 메모리 캐시 확인
        with self.memory_lock:
            if cache_key in self.memory_cache:
                self.stats.hits += 1
                self.stats.memory_hits += 1
                logger.debug(f"Memory cache hit for key: {cache_key[:16]}...")
                return self.memory_cache[cache_key]

        # L2: Redis 캐시 확인
        if self.redis_client:
            try:
                cached_data = await self.redis_client.get(f"emb:{cache_key}")
                if cached_data:
                    embedding = self._deserialize_embedding(cached_data)
                    if embedding is not None:
                        # 메모리 캐시에도 저장
                        with self.memory_lock:
                            self.memory_cache[cache_key] = embedding

                        self.stats.hits += 1
                        self.stats.redis_hits += 1
                        logger.debug(f"Redis cache hit for key: {cache_key[:16]}...")
                        return embedding
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")

        # 캐시 미스
        self.stats.misses += 1
        logger.debug(f"Cache miss for key: {cache_key[:16]}...")
        return None

    async def set_embedding(self, text: str, embedding: np.ndarray) -> bool:
        """임베딩 저장 (메모리 + Redis 동시 저장)"""
        cache_key = self._generate_cache_key(text)

        try:
            # 메모리 캐시 저장
            with self.memory_lock:
                self.memory_cache[cache_key] = embedding.copy()

            # Redis 캐시 저장
            if self.redis_client:
                serialized_data = self._serialize_embedding(embedding)
                await self.redis_client.setex(
                    f"emb:{cache_key}",
                    self.redis_ttl,
                    serialized_data
                )

            self.stats.sets += 1
            logger.debug(f"Embedding cached for key: {cache_key[:16]}...")
            return True

        except Exception as e:
            logger.error(f"Failed to cache embedding: {e}")
            return False

    async def get_or_create_embedding(
        self,
        text: str,
        embedding_func: callable,
        *args,
        **kwargs
    ) -> Optional[np.ndarray]:
        """임베딩 조회 또는 생성 (캐시 우선)"""
        # 캐시에서 조회 시도
        cached_embedding = await self.get_embedding(text)
        if cached_embedding is not None:
            return cached_embedding

        # 캐시 미스 - 새로 생성
        try:
            start_time = time.time()
            embedding = await embedding_func(text, *args, **kwargs)
            generation_time = time.time() - start_time

            if embedding is not None:
                # 캐시에 저장
                await self.set_embedding(text, embedding)
                logger.debug(f"Generated and cached embedding in {generation_time:.3f}s")
                return embedding

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")

        return None

    async def batch_get_embeddings(
        self,
        texts: List[str],
        embedding_func: callable,
        batch_size: int = 100,
        *args,
        **kwargs
    ) -> List[Optional[np.ndarray]]:
        """배치 임베딩 조회/생성 (캐시 최적화)"""
        results = [None] * len(texts)
        cache_misses = []
        cache_miss_indices = []

        # 캐시에서 조회
        for i, text in enumerate(texts):
            cached_embedding = await self.get_embedding(text)
            if cached_embedding is not None:
                results[i] = cached_embedding
            else:
                cache_misses.append(text)
                cache_miss_indices.append(i)

        # 캐시 미스된 항목들을 배치로 처리
        if cache_misses:
            logger.info(f"Cache hits: {len(texts) - len(cache_misses)}/{len(texts)}, generating {len(cache_misses)} embeddings")

            # 배치 크기로 분할하여 처리
            for batch_start in range(0, len(cache_misses), batch_size):
                batch_end = min(batch_start + batch_size, len(cache_misses))
                batch_texts = cache_misses[batch_start:batch_end]

                try:
                    # 배치로 임베딩 생성
                    batch_embeddings = await embedding_func(batch_texts, *args, **kwargs)

                    # 결과 저장 및 캐싱
                    for i, embedding in enumerate(batch_embeddings):
                        original_index = cache_miss_indices[batch_start + i]
                        results[original_index] = embedding

                        # 캐시에 저장
                        if embedding is not None:
                            await self.set_embedding(batch_texts[i], embedding)

                except Exception as e:
                    logger.error(f"Batch embedding generation failed: {e}")
                    # 개별적으로 재시도
                    for i, text in enumerate(batch_texts):
                        try:
                            embedding = await embedding_func([text], *args, **kwargs)
                            if embedding and len(embedding) > 0:
                                original_index = cache_miss_indices[batch_start + i]
                                results[original_index] = embedding[0]
                                await self.set_embedding(text, embedding[0])
                        except Exception as e2:
                            logger.warning(f"Individual embedding generation failed for text: {e2}")

        return results

    def _generate_cache_key(self, text: str) -> str:
        """텍스트에서 캐시 키 생성"""
        # 텍스트 정규화 (공백, 대소문자 등)
        normalized_text = text.strip().lower()

        # SHA256 해시 생성
        hash_object = hashlib.sha256(normalized_text.encode('utf-8'))
        return hash_object.hexdigest()

    def _serialize_embedding(self, embedding: np.ndarray) -> bytes:
        """임베딩을 바이트로 직렬화"""
        try:
            if self.enable_compression:
                # numpy 압축 저장
                import io
                buffer = io.BytesIO()
                np.savez_compressed(buffer, embedding=embedding)
                return buffer.getvalue()
            else:
                # 단순 바이트 변환
                return embedding.astype(np.float32).tobytes()
        except Exception as e:
            logger.error(f"Embedding serialization failed: {e}")
            return b''

    def _deserialize_embedding(self, data: bytes) -> Optional[np.ndarray]:
        """바이트에서 임베딩 복원"""
        try:
            if self.enable_compression:
                # numpy 압축 파일 로드
                import io
                buffer = io.BytesIO(data)
                loaded = np.load(buffer)
                return loaded['embedding']
            else:
                # 단순 바이트 변환
                return np.frombuffer(data, dtype=np.float32)
        except Exception as e:
            logger.error(f"Embedding deserialization failed: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        return {
            'total_requests': self.stats.total_requests,
            'hits': self.stats.hits,
            'misses': self.stats.misses,
            'sets': self.stats.sets,
            'hit_rate': self.stats.hit_rate,
            'memory_hits': self.stats.memory_hits,
            'redis_hits': self.stats.redis_hits,
            'memory_hit_rate': self.stats.memory_hit_rate,
            'memory_cache_size': len(self.memory_cache),
            'redis_available': self.redis_client is not None
        }

    async def clear_cache(self, pattern: str = "emb:*") -> int:
        """캐시 클리어"""
        cleared_count = 0

        # 메모리 캐시 클리어
        with self.memory_lock:
            cleared_count += len(self.memory_cache)
            self.memory_cache.clear()

        # Redis 캐시 클리어
        if self.redis_client:
            try:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    cleared_count += await self.redis_client.delete(*keys)
            except Exception as e:
                logger.error(f"Redis cache clear failed: {e}")

        logger.info(f"Cleared {cleared_count} cache entries")
        return cleared_count

    async def close(self):
        """리소스 정리"""
        if self.redis_client:
            try:
                # FakeRedis는 close() 대신 aclose() 사용
                if hasattr(self.redis_client, 'aclose'):
                    await self.redis_client.aclose()
                elif hasattr(self.redis_client, 'close'):
                    if asyncio.iscoroutinefunction(self.redis_client.close):
                        await self.redis_client.close()
                    else:
                        self.redis_client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Redis close failed: {e}")


# 전역 캐시 인스턴스
_embedding_cache = None

def get_embedding_cache() -> EmbeddingCache:
    """전역 임베딩 캐시 인스턴스 반환"""
    global _embedding_cache
    if _embedding_cache is None:
        _embedding_cache = EmbeddingCache()
    return _embedding_cache

async def initialize_embedding_cache(
    redis_url: str = "redis://localhost:6379",
    memory_cache_size: int = 10000,
    **kwargs
) -> EmbeddingCache:
    """임베딩 캐시 초기화"""
    global _embedding_cache
    _embedding_cache = EmbeddingCache(
        redis_url=redis_url,
        memory_cache_size=memory_cache_size,
        **kwargs
    )
    return _embedding_cache