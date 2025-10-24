"""
고성능 검색 캐싱 시스템
검색 결과, 임베딩, 쿼리 제안을 메모리와 Redis에 캐싱
"""

import asyncio
import hashlib
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Redis 호환 인터페이스 (실제 Redis 또는 메모리 폴백)
try:
    import redis.asyncio  # noqa: F401
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using memory cache only")

@dataclass
class CacheConfig:
    """캐시 설정"""
    # 메모리 캐시 설정
    max_memory_entries: int = 1000
    memory_ttl_seconds: int = 300  # 5분

    # Redis 설정 (사용 가능한 경우)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_ttl_seconds: int = 3600  # 1시간

    # 캐시 키 프리픽스
    search_prefix: str = "search:"
    embedding_prefix: str = "embedding:"
    query_suggestion_prefix: str = "query_suggest:"

    # 압축 설정
    enable_compression: bool = True
    compression_threshold: int = 1024  # 1KB 이상일 때 압축

class MemoryCache:
    """메모리 기반 LRU 캐시"""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = {}
        self.access_times = {}
        self.creation_times = {}

    def _is_expired(self, key: str) -> bool:
        """TTL 만료 확인"""
        if key not in self.creation_times:
            return True
        return time.time() - self.creation_times[key] > self.ttl_seconds

    def _evict_expired(self):
        """만료된 항목 제거"""
        current_time = time.time()
        expired_keys = [
            key for key, creation_time in self.creation_times.items()
            if current_time - creation_time > self.ttl_seconds
        ]
        for key in expired_keys:
            self.cache.pop(key, None)
            self.access_times.pop(key, None)
            self.creation_times.pop(key, None)

    def _evict_lru(self):
        """LRU 기반 공간 확보"""
        while len(self.cache) >= self.max_size:
            # 가장 오래된 접근 시간을 가진 키 찾기
            oldest_key = min(self.access_times.keys(),
                           key=lambda k: self.access_times[k])
            self.cache.pop(oldest_key, None)
            self.access_times.pop(oldest_key, None)
            self.creation_times.pop(oldest_key, None)

    async def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회"""
        if key not in self.cache or self._is_expired(key):
            return None

        self.access_times[key] = time.time()
        return self.cache[key]

    async def set(self, key: str, value: Any):
        """캐시에 값 저장"""
        self._evict_expired()
        self._evict_lru()

        current_time = time.time()
        self.cache[key] = value
        self.access_times[key] = current_time
        self.creation_times[key] = current_time

    async def delete(self, key: str):
        """캐시에서 값 삭제"""
        self.cache.pop(key, None)
        self.access_times.pop(key, None)
        self.creation_times.pop(key, None)

    async def clear(self):
        """전체 캐시 클리어"""
        self.cache.clear()
        self.access_times.clear()
        self.creation_times.clear()

    def stats(self) -> Dict[str, Any]:
        """캐시 통계"""
        self._evict_expired()
        return {
            "entries": len(self.cache),
            "max_size": self.max_size,
            "hit_rate": 0.0,  # 추적하려면 별도 구현 필요
            "memory_usage_mb": 0.0  # 대략적 계산
        }

class RedisCache:
    """Redis 기반 캐시 (최적화된 Redis 매니저 사용)"""

    def __init__(self, config: CacheConfig):
        self.config = config
        self.redis_manager = None
        self._initialized = False

    async def _ensure_connection(self):
        """Redis 연결 확인"""
        if not self._initialized and REDIS_AVAILABLE:
            try:
                from .redis_manager import get_redis_manager
                self.redis_manager = await get_redis_manager()
                self._initialized = True
                logger.info("Redis cache initialized with Redis manager")
            except Exception as e:
                logger.warning(f"Redis manager initialization failed: {e}")
                self.redis_manager = None

    async def get(self, key: str) -> Optional[Any]:
        """Redis에서 값 조회"""
        await self._ensure_connection()
        if self.redis_manager is None:
            return None

        try:
            return await self.redis_manager.get(key)
        except Exception as e:
            logger.warning(f"Redis get failed for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any):
        """Redis에 값 저장"""
        await self._ensure_connection()
        if self.redis_manager is None:
            return

        try:
            # TTL 결정
            ttl = self.config.redis_ttl_seconds
            if 'embedding' in key:
                ttl = 86400 * 7  # 임베딩은 1주일
            elif 'query_suggest' in key:
                ttl = 3600  # 쿼리 제안은 1시간

            await self.redis_manager.set(key, value, ttl=ttl)
        except Exception as e:
            logger.warning(f"Redis set failed for key {key}: {e}")

    async def delete(self, key: str):
        """Redis에서 값 삭제"""
        await self._ensure_connection()
        if self.redis_manager is None:
            return

        try:
            await self.redis_manager.delete(key)
        except Exception as e:
            logger.warning(f"Redis delete failed for key {key}: {e}")

    async def clear_pattern(self, pattern: str):
        """패턴 매칭으로 키 삭제"""
        await self._ensure_connection()
        if self.redis_manager is None:
            return

        try:
            await self.redis_manager.delete_pattern(pattern)
        except Exception as e:
            logger.warning(f"Redis clear pattern failed for {pattern}: {e}")

    async def stats(self) -> Dict[str, Any]:
        """Redis 캐시 통계"""
        await self._ensure_connection()
        if self.redis_manager is None:
            return {}

        try:
            health_info = await self.redis_manager.health_check()
            manager_stats = self.redis_manager.get_stats()

            return {
                "connection_status": health_info.get("status", "unknown"),
                "response_time_ms": health_info.get("response_time_ms", 0),
                "operations_total": manager_stats.get("operations_total", 0),
                "success_rate_percent": manager_stats.get("success_rate_percent", 0),
                "compression_ratio": manager_stats.get("compression_ratio", 0),
                "compression_enabled": manager_stats.get("compression_enabled", False)
            }
        except Exception as e:
            logger.warning(f"Redis stats failed: {e}")
            return {}

class HybridSearchCache:
    """하이브리드 검색 캐시 시스템"""

    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()

        # 2-레벨 캐시: 메모리(L1) + Redis(L2)
        self.memory_cache = MemoryCache(
            max_size=self.config.max_memory_entries,
            ttl_seconds=self.config.memory_ttl_seconds
        )
        self.redis_cache = RedisCache(self.config)

        # 캐시 통계
        self.stats = {
            "l1_hits": 0, "l1_misses": 0,
            "l2_hits": 0, "l2_misses": 0,
            "sets": 0, "evictions": 0
        }

    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """캐시 키 생성"""
        # 정렬된 파라미터로 일관된 키 생성
        key_data = json.dumps(kwargs, sort_keys=True, ensure_ascii=False)
        key_hash = hashlib.md5(key_data.encode(), usedforsecurity=False).hexdigest()
        return f"{prefix}{key_hash}"

    async def get_search_results(
        self,
        query: str,
        filters: Dict = None,
        search_params: Dict = None
    ) -> Optional[List[Dict[str, Any]]]:
        """검색 결과 캐시 조회"""
        cache_key = self._generate_cache_key(
            self.config.search_prefix,
            query=query,
            filters=filters or {},
            params=search_params or {}
        )

        # L1 캐시 확인 (메모리)
        result = await self.memory_cache.get(cache_key)
        if result is not None:
            self.stats["l1_hits"] += 1
            return result

        self.stats["l1_misses"] += 1

        # L2 캐시 확인 (Redis)
        result = await self.redis_cache.get(cache_key)
        if result is not None:
            self.stats["l2_hits"] += 1
            # L1 캐시에도 저장 (캐시 승격)
            await self.memory_cache.set(cache_key, result)
            return result

        self.stats["l2_misses"] += 1
        return None

    async def set_search_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        filters: Dict = None,
        search_params: Dict = None
    ):
        """검색 결과 캐시 저장"""
        cache_key = self._generate_cache_key(
            self.config.search_prefix,
            query=query,
            filters=filters or {},
            params=search_params or {}
        )

        # 양쪽 캐시에 저장
        await asyncio.gather(
            self.memory_cache.set(cache_key, results),
            self.redis_cache.set(cache_key, results)
        )
        self.stats["sets"] += 1

    async def get_embedding(self, text: str, model: str = "openai") -> Optional[List[float]]:
        """임베딩 캐시 조회"""
        cache_key = self._generate_cache_key(
            self.config.embedding_prefix,
            text=text,
            model=model
        )

        # 임베딩은 L2(Redis)만 사용 (크기가 크고 재사용 빈도 높음)
        result = await self.redis_cache.get(cache_key)
        if result is not None:
            self.stats["l2_hits"] += 1
            return result

        self.stats["l2_misses"] += 1
        return None

    async def set_embedding(self, text: str, embedding: List[float], model: str = "openai"):
        """임베딩 캐시 저장"""
        cache_key = self._generate_cache_key(
            self.config.embedding_prefix,
            text=text,
            model=model
        )

        await self.redis_cache.set(cache_key, embedding)
        self.stats["sets"] += 1

    async def get_query_suggestions(self, partial_query: str) -> Optional[List[str]]:
        """쿼리 제안 캐시 조회"""
        cache_key = self._generate_cache_key(
            self.config.query_suggestion_prefix,
            partial=partial_query.lower().strip()
        )

        result = await self.memory_cache.get(cache_key)
        if result is None:
            result = await self.redis_cache.get(cache_key)
            if result is not None:
                await self.memory_cache.set(cache_key, result)

        return result

    async def set_query_suggestions(self, partial_query: str, suggestions: List[str]):
        """쿼리 제안 캐시 저장"""
        cache_key = self._generate_cache_key(
            self.config.query_suggestion_prefix,
            partial=partial_query.lower().strip()
        )

        await asyncio.gather(
            self.memory_cache.set(cache_key, suggestions),
            self.redis_cache.set(cache_key, suggestions)
        )

    async def invalidate_search_cache(self, pattern: str = None):
        """검색 캐시 무효화"""
        if pattern:
            # 특정 패턴 매칭으로 삭제
            await self.redis_cache.clear_pattern(f"{self.config.search_prefix}*{pattern}*")
        else:
            # 전체 검색 캐시 삭제
            await self.redis_cache.clear_pattern(f"{self.config.search_prefix}*")

        # 메모리 캐시는 전체 클리어 (패턴 매칭 복잡)
        await self.memory_cache.clear()

        self.stats["evictions"] += 1

    async def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 성능 통계"""
        memory_stats = self.memory_cache.stats()
        redis_stats = await self.redis_cache.stats()

        total_operations = sum([
            self.stats["l1_hits"], self.stats["l1_misses"],
            self.stats["l2_hits"], self.stats["l2_misses"]
        ])

        if total_operations > 0:
            l1_hit_rate = self.stats["l1_hits"] / total_operations
            l2_hit_rate = self.stats["l2_hits"] / total_operations
            overall_hit_rate = (self.stats["l1_hits"] + self.stats["l2_hits"]) / total_operations
        else:
            l1_hit_rate = l2_hit_rate = overall_hit_rate = 0.0

        return {
            "memory_cache": memory_stats,
            "redis_cache": redis_stats,
            "hit_rates": {
                "l1_hit_rate": round(l1_hit_rate, 3),
                "l2_hit_rate": round(l2_hit_rate, 3),
                "overall_hit_rate": round(overall_hit_rate, 3)
            },
            "operations": self.stats.copy(),
            "cache_efficiency": {
                "cache_utilization": round(overall_hit_rate, 3),
                "memory_efficiency": round(l1_hit_rate / max(overall_hit_rate, 0.001), 3)
            }
        }

    async def warm_up(self, common_queries: List[str]):
        """캐시 웜업"""
        logger.info(f"Warming up cache with {len(common_queries)} queries")

        for query in common_queries:
            # 쿼리별로 빈 결과라도 캐시에 저장하여 후속 요청 가속화
            await self.set_query_suggestions(query[:10], [])  # 부분 쿼리 제안

        logger.info("Cache warm-up completed")

# 전역 캐시 인스턴스 (싱글톤)
_cache_instance = None

async def get_search_cache() -> HybridSearchCache:
    """전역 검색 캐시 인스턴스 조회"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = HybridSearchCache()
    return _cache_instance

async def configure_search_cache(config: CacheConfig):
    """전역 검색 캐시 설정"""
    global _cache_instance
    _cache_instance = HybridSearchCache(config)

# 캐시 데코레이터
def cache_search_results(ttl_seconds: int = 300):
    """검색 결과 캐싱 데코레이터"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache = await get_search_cache()

            # 캐시 키 생성 (함수명 + 인자들)
            cache_key_data = {
                "function": func.__name__,
                "args": str(args),
                "kwargs": kwargs
            }

            query = kwargs.get('query', args[1] if len(args) > 1 else '')
            filters = kwargs.get('filters', {})

            # 캐시에서 결과 조회
            cached_result = await cache.get_search_results(
                query=query,
                filters=filters,
                search_params=cache_key_data
            )

            if cached_result is not None:
                return cached_result

            # 실제 함수 실행
            result = await func(*args, **kwargs)

            # 결과 캐싱
            await cache.set_search_results(
                query=query,
                results=result,
                filters=filters,
                search_params=cache_key_data
            )

            return result

        return wrapper
    return decorator

def cache_embeddings(ttl_seconds: int = 3600):
    """임베딩 캐싱 데코레이터"""
    def decorator(func):
        async def wrapper(text: str, model: str = "openai", *args, **kwargs):
            cache = await get_search_cache()

            # 캐시에서 임베딩 조회
            cached_embedding = await cache.get_embedding(text, model)
            if cached_embedding is not None:
                return cached_embedding

            # 실제 임베딩 생성
            embedding = await func(text, model, *args, **kwargs)

            # 임베딩 캐싱
            await cache.set_embedding(text, embedding, model)

            return embedding

        return wrapper
    return decorator