"""
하이브리드 검색 성능 최적화 및 캐싱 시스템
Redis 캐싱, 인덱스 최적화, 배치 처리 등
"""

import asyncio
import hashlib
import json
import time
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
import redis.asyncio as aioredis
from functools import wraps
import numpy as np
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

@dataclass
class CacheConfig:
    """캐시 설정"""
    redis_url: str = "redis://localhost:6379"
    default_ttl: int = 3600  # 1시간
    max_cache_size: int = 10000  # 최대 캐시 항목 수
    enable_compression: bool = True
    enable_embedding_cache: bool = True
    enable_result_cache: bool = True

class SearchCache:
    """검색 결과 캐싱 시스템"""

    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self.redis_client = None
        self.local_cache = {}  # 폴백 로컬 캐시
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'errors': 0
        }

    async def initialize(self):
        """Redis 연결 초기화"""
        try:
            self.redis_client = aioredis.from_url(
                self.config.redis_url,
                decode_responses=True,
                health_check_interval=30
            )
            await self.redis_client.ping()
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.warning(f"Redis cache initialization failed: {e}")
            self.redis_client = None

    async def get_search_results(
        self,
        query_hash: str,
        cache_type: str = "hybrid"
    ) -> Optional[List[Dict[str, Any]]]:
        """검색 결과 캐시 조회"""
        try:
            cache_key = f"search:{cache_type}:{query_hash}"

            if self.redis_client:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    self.cache_stats['hits'] += 1
                    return json.loads(cached_data)

            # 로컬 캐시 폴백
            if cache_key in self.local_cache:
                entry = self.local_cache[cache_key]
                if time.time() - entry['timestamp'] < self.config.default_ttl:
                    self.cache_stats['hits'] += 1
                    return entry['data']
                else:
                    del self.local_cache[cache_key]

            self.cache_stats['misses'] += 1
            return None

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.cache_stats['errors'] += 1
            return None

    async def set_search_results(
        self,
        query_hash: str,
        results: List[Dict[str, Any]],
        cache_type: str = "hybrid",
        ttl: int = None
    ):
        """검색 결과 캐시 저장"""
        try:
            cache_key = f"search:{cache_type}:{query_hash}"
            ttl = ttl or self.config.default_ttl

            serialized_data = json.dumps(results, ensure_ascii=False)

            if self.redis_client:
                await self.redis_client.setex(cache_key, ttl, serialized_data)
            else:
                # 로컬 캐시에 저장
                if len(self.local_cache) >= self.config.max_cache_size:
                    # LRU 방식으로 가장 오래된 항목 제거
                    oldest_key = min(
                        self.local_cache.keys(),
                        key=lambda k: self.local_cache[k]['timestamp']
                    )
                    del self.local_cache[oldest_key]

                self.local_cache[cache_key] = {
                    'data': results,
                    'timestamp': time.time()
                }

            self.cache_stats['sets'] += 1

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            self.cache_stats['errors'] += 1

    async def get_embedding(self, text_hash: str) -> Optional[np.ndarray]:
        """임베딩 캐시 조회"""
        if not self.config.enable_embedding_cache:
            return None

        try:
            cache_key = f"embedding:{text_hash}"

            if self.redis_client:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    embedding_data = json.loads(cached_data)
                    return np.array(embedding_data, dtype=np.float32)

            return None

        except Exception as e:
            logger.error(f"Embedding cache get error: {e}")
            return None

    async def set_embedding(self, text_hash: str, embedding: np.ndarray, ttl: int = None):
        """임베딩 캐시 저장"""
        if not self.config.enable_embedding_cache:
            return

        try:
            cache_key = f"embedding:{text_hash}"
            ttl = ttl or (self.config.default_ttl * 24)  # 임베딩은 더 오래 캐시

            embedding_data = embedding.tolist()
            serialized_data = json.dumps(embedding_data)

            if self.redis_client:
                await self.redis_client.setex(cache_key, ttl, serialized_data)

        except Exception as e:
            logger.error(f"Embedding cache set error: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """캐시 통계 조회"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = self.cache_stats['hits'] / total_requests if total_requests > 0 else 0

        return {
            **self.cache_stats,
            'hit_rate': hit_rate,
            'total_requests': total_requests
        }

    async def clear_cache(self, pattern: str = "search:*"):
        """캐시 클리어"""
        try:
            if self.redis_client:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)

            # 로컬 캐시도 클리어
            if pattern == "search:*":
                self.local_cache.clear()

            logger.info(f"Cache cleared for pattern: {pattern}")

        except Exception as e:
            logger.error(f"Cache clear error: {e}")


class QueryOptimizer:
    """쿼리 최적화기"""

    @staticmethod
    def optimize_query(query: str) -> str:
        """쿼리 최적화"""
        # 불필요한 공백 제거
        optimized = " ".join(query.split())

        # 소문자 변환 (언어별 처리 필요시 확장)
        optimized = optimized.lower()

        # 특수문자 정리 (검색에 유용하지 않은 문자)
        import re
        optimized = re.sub(r'[^\w\s가-힣]', ' ', optimized)

        # 중복 단어 제거 (순서 유지)
        words = []
        seen = set()
        for word in optimized.split():
            if word not in seen and len(word) >= 2:
                words.append(word)
                seen.add(word)

        return " ".join(words)

    @staticmethod
    def generate_query_hash(
        query: str,
        filters: Dict[str, Any] = None,
        config_params: Dict[str, Any] = None
    ) -> str:
        """쿼리 해시 생성 (캐시 키용)"""
        # 쿼리와 필터, 설정을 결합하여 해시 생성
        hash_input = {
            'query': query,
            'filters': filters or {},
            'config': config_params or {}
        }

        hash_string = json.dumps(hash_input, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(hash_string.encode('utf-8')).hexdigest()

    @staticmethod
    def analyze_query_complexity(query: str) -> Dict[str, Any]:
        """쿼리 복잡도 분석"""
        words = query.split()

        complexity_score = 0
        complexity_score += len(words) * 0.1  # 단어 수
        complexity_score += len([w for w in words if len(w) > 6]) * 0.2  # 긴 단어
        complexity_score += query.count('"') * 0.3  # 구문 검색
        complexity_score += len([w for w in words if w.lower() in ['and', 'or', 'not']]) * 0.4  # 불린 연산

        return {
            'word_count': len(words),
            'avg_word_length': sum(len(w) for w in words) / len(words) if words else 0,
            'has_phrases': '"' in query,
            'has_boolean': any(op in query.lower() for op in ['and', 'or', 'not']),
            'complexity_score': min(complexity_score, 1.0),
            'estimated_difficulty': 'easy' if complexity_score < 0.3 else 'medium' if complexity_score < 0.7 else 'hard'
        }


class IndexOptimizer:
    """인덱스 최적화기"""

    @staticmethod
    async def optimize_database_indices(session):
        """데이터베이스 인덱스 최적화"""
        optimizations = []

        try:
            # PostgreSQL용 인덱스 최적화
            if "postgresql" in str(session.bind.url):
                await IndexOptimizer._optimize_postgresql_indices(session)
                optimizations.append("PostgreSQL indices optimized")

            # SQLite용 인덱스 최적화
            else:
                await IndexOptimizer._optimize_sqlite_indices(session)
                optimizations.append("SQLite indices optimized")

            return optimizations

        except Exception as e:
            logger.error(f"Index optimization failed: {e}")
            return []

    @staticmethod
    async def _optimize_postgresql_indices(session):
        """PostgreSQL 인덱스 최적화"""
        # GIN 인덱스 최적화 (full-text search)
        await session.execute("REINDEX INDEX CONCURRENTLY IF EXISTS idx_chunks_text_gin;")

        # Vector 인덱스 최적화
        await session.execute("REINDEX INDEX CONCURRENTLY IF EXISTS idx_chunks_embedding;")

        # 통계 업데이트
        await session.execute("ANALYZE chunks;")
        await session.execute("ANALYZE documents;")

    @staticmethod
    async def _optimize_sqlite_indices(session):
        """SQLite 인덱스 최적화"""
        # 인덱스 재구성
        await session.execute("REINDEX;")

        # 통계 업데이트
        await session.execute("ANALYZE;")


class BatchProcessor:
    """배치 처리 최적화"""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def process_embedding_batch(
        self,
        texts: List[str],
        embedding_service,
        batch_size: int = 50
    ) -> List[np.ndarray]:
        """임베딩 배치 처리"""
        results = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            # 배치별 병렬 처리
            tasks = []
            for text in batch:
                task = embedding_service.generate_embedding(text)
                tasks.append(task)

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Embedding generation failed: {result}")
                    results.append(np.zeros(1536, dtype=np.float32))  # 더미 임베딩
                else:
                    results.append(result)

        return results

    async def process_search_batch(
        self,
        queries: List[str],
        search_engine,
        session
    ) -> List[Dict[str, Any]]:
        """검색 배치 처리"""
        tasks = []
        for query in queries:
            task = search_engine.search(session, query)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch search failed: {result}")
                processed_results.append({'error': str(result)})
            else:
                processed_results.append(result)

        return processed_results


class PerformanceMonitor:
    """성능 모니터링"""

    def __init__(self):
        self.metrics = {
            'search_count': 0,
            'total_time': 0.0,
            'avg_time': 0.0,
            'max_time': 0.0,
            'min_time': float('inf'),
            'error_count': 0,
            'cache_hit_rate': 0.0
        }
        self.recent_queries = []

    def record_search(
        self,
        query: str,
        duration: float,
        result_count: int,
        error: bool = False
    ):
        """검색 성능 기록"""
        self.metrics['search_count'] += 1

        if error:
            self.metrics['error_count'] += 1
        else:
            self.metrics['total_time'] += duration
            self.metrics['avg_time'] = self.metrics['total_time'] / (
                self.metrics['search_count'] - self.metrics['error_count']
            )
            self.metrics['max_time'] = max(self.metrics['max_time'], duration)
            self.metrics['min_time'] = min(self.metrics['min_time'], duration)

        # 최근 쿼리 기록 (최대 100개)
        self.recent_queries.append({
            'query': query[:100],  # 쿼리 길이 제한
            'duration': duration,
            'result_count': result_count,
            'timestamp': time.time(),
            'error': error
        })

        if len(self.recent_queries) > 100:
            self.recent_queries = self.recent_queries[-100:]

    def get_performance_report(self) -> Dict[str, Any]:
        """성능 리포트 생성"""
        if not self.recent_queries:
            return self.metrics

        recent_times = [q['duration'] for q in self.recent_queries if not q['error']]

        if recent_times:
            recent_times.sort()
            p50 = recent_times[len(recent_times) // 2]
            p95 = recent_times[int(len(recent_times) * 0.95)]
            p99 = recent_times[int(len(recent_times) * 0.99)]
        else:
            p50 = p95 = p99 = 0

        return {
            **self.metrics,
            'recent_p50': p50,
            'recent_p95': p95,
            'recent_p99': p99,
            'error_rate': self.metrics['error_count'] / self.metrics['search_count'] if self.metrics['search_count'] > 0 else 0,
            'queries_per_second': len([q for q in self.recent_queries if time.time() - q['timestamp'] < 60]) / 60
        }

    def get_slow_queries(self, threshold: float = 2.0) -> List[Dict[str, Any]]:
        """느린 쿼리 조회"""
        return [
            q for q in self.recent_queries
            if q['duration'] > threshold and not q['error']
        ]


def cache_result(cache_type: str = "hybrid", ttl: int = None):
    """검색 결과 캐싱 데코레이터"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 검색 엔진과 캐시 인스턴스 추출
            search_engine = args[0] if args else None
            cache = getattr(search_engine, 'cache', None) if search_engine else None

            if not cache:
                return await func(*args, **kwargs)

            # 캐시 키 생성
            query = kwargs.get('query') or (args[2] if len(args) > 2 else '')
            filters = kwargs.get('filters') or (args[3] if len(args) > 3 else {})

            query_hash = QueryOptimizer.generate_query_hash(query, filters)

            # 캐시에서 조회
            cached_result = await cache.get_search_results(query_hash, cache_type)
            if cached_result:
                return cached_result

            # 실제 검색 수행
            result = await func(*args, **kwargs)

            # 결과 캐싱
            if result and not isinstance(result, Exception):
                await cache.set_search_results(query_hash, result, cache_type, ttl)

            return result

        return wrapper
    return decorator


# 전역 인스턴스들
_cache_instance = None
_performance_monitor = None

async def get_cache() -> SearchCache:
    """전역 캐시 인스턴스 조회"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = SearchCache()
        await _cache_instance.initialize()
    return _cache_instance

def get_performance_monitor() -> PerformanceMonitor:
    """전역 성능 모니터 인스턴스 조회"""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor