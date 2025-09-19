"""
배치 처리 최적화 시스템
HYBRID_SEARCH_OPTIMIZATION_GUIDE.md 배치 처리 구현

핵심 기능:
- 다중 쿼리 배치 검색
- 배치 임베딩 생성
- 연결 풀 최적화
- 처리량 최적화
"""

import asyncio
import time
import logging
from typing import List, Dict, Any, Optional, Tuple, AsyncGenerator
from dataclasses import dataclass
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class BatchConfig:
    """배치 처리 설정"""
    max_batch_size: int = 50
    max_wait_time_ms: int = 100
    auto_flush: bool = True
    enable_prioritization: bool = True

@dataclass
class BatchMetrics:
    """배치 처리 메트릭"""
    total_batches: int = 0
    total_items_processed: int = 0
    avg_batch_size: float = 0.0
    avg_processing_time_ms: float = 0.0
    throughput_items_per_sec: float = 0.0
    cache_hit_rate: float = 0.0

class BatchSearchProcessor:
    """배치 검색 처리기"""

    def __init__(self, config: BatchConfig = None):
        self.config = config or BatchConfig()
        self.metrics = BatchMetrics()
        self.pending_requests = []
        self.result_futures = {}
        self.processing_lock = asyncio.Lock()
        self.flush_task = None

        # 임베딩 캐시
        self.embedding_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0

    async def submit_search_request(
        self,
        query: str,
        search_params: Dict[str, Any],
        priority: int = 0
    ) -> List[Dict[str, Any]]:
        """
        검색 요청을 배치에 추가

        Args:
            query: 검색 쿼리
            search_params: 검색 파라미터
            priority: 우선순위 (높을수록 먼저 처리)

        Returns:
            검색 결과
        """
        request_id = self._generate_request_id(query, search_params)

        # 결과 Future 생성
        result_future = asyncio.Future()
        self.result_futures[request_id] = result_future

        # 요청을 배치에 추가
        async with self.processing_lock:
            self.pending_requests.append({
                "id": request_id,
                "query": query,
                "search_params": search_params,
                "priority": priority,
                "timestamp": time.time()
            })

            # 우선순위 정렬
            if self.config.enable_prioritization:
                self.pending_requests.sort(key=lambda x: (-x["priority"], x["timestamp"]))

            # 배치 크기 도달 시 즉시 플러시
            if len(self.pending_requests) >= self.config.max_batch_size:
                await self._flush_batch()
            elif self.flush_task is None and self.config.auto_flush:
                # 자동 플러시 스케줄링
                self.flush_task = asyncio.create_task(self._auto_flush())

        # 결과 대기
        return await result_future

    async def _auto_flush(self):
        """자동 배치 플러시"""
        try:
            await asyncio.sleep(self.config.max_wait_time_ms / 1000.0)
            async with self.processing_lock:
                if self.pending_requests:
                    await self._flush_batch()
        except asyncio.CancelledError:
            pass
        finally:
            self.flush_task = None

    async def _flush_batch(self):
        """배치 플러시 및 처리"""
        if not self.pending_requests:
            return

        # 현재 배치 복사 및 초기화
        current_batch = self.pending_requests.copy()
        self.pending_requests.clear()

        # 자동 플러시 태스크 취소
        if self.flush_task:
            self.flush_task.cancel()
            self.flush_task = None

        start_time = time.time()

        try:
            # 배치 처리 실행
            await self._process_batch(current_batch)

            # 메트릭 업데이트
            processing_time = (time.time() - start_time) * 1000
            self._update_metrics(len(current_batch), processing_time)

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            # 모든 요청에 오류 전파
            for request in current_batch:
                future = self.result_futures.pop(request["id"], None)
                if future and not future.done():
                    future.set_exception(e)

    async def _process_batch(self, batch: List[Dict[str, Any]]):
        """실제 배치 처리"""
        try:
            # 1. 임베딩 배치 생성
            embeddings = await self._generate_batch_embeddings(batch)

            # 2. 병렬 검색 실행
            search_tasks = []
            for i, request in enumerate(batch):
                search_task = self._execute_single_search(
                    request, embeddings[i]
                )
                search_tasks.append(search_task)

            # 3. 모든 검색 병렬 실행
            search_results = await asyncio.gather(
                *search_tasks,
                return_exceptions=True
            )

            # 4. 결과 분배
            for request, result in zip(batch, search_results):
                future = self.result_futures.pop(request["id"], None)
                if future and not future.done():
                    if isinstance(result, Exception):
                        future.set_exception(result)
                    else:
                        future.set_result(result)

        except Exception as e:
            logger.error(f"Batch processing execution failed: {e}")
            raise

    async def _generate_batch_embeddings(
        self,
        batch: List[Dict[str, Any]]
    ) -> List[List[float]]:
        """배치 임베딩 생성"""
        embeddings = []

        for request in batch:
            query = request["query"]

            # 캐시 확인
            cache_key = hashlib.md5(query.encode()).hexdigest()
            if cache_key in self.embedding_cache:
                embeddings.append(self.embedding_cache[cache_key])
                self.cache_hits += 1
            else:
                # 임베딩 생성
                from ..database import EmbeddingService
                embedding = await EmbeddingService.generate_embedding(query)

                # 캐시 저장
                self.embedding_cache[cache_key] = embedding
                if len(self.embedding_cache) > 1000:  # 캐시 크기 제한
                    # LRU 방식으로 절반 제거
                    items = list(self.embedding_cache.items())
                    self.embedding_cache = dict(items[500:])

                embeddings.append(embedding)
                self.cache_misses += 1

        return embeddings

    async def _execute_single_search(
        self,
        request: Dict[str, Any],
        query_embedding: List[float]
    ) -> List[Dict[str, Any]]:
        """단일 검색 실행"""
        from ..database import SearchDAO, db_manager

        try:
            async with db_manager.async_session() as session:
                # 하이브리드 검색 실행 (최적화된 버전 사용)
                result = await SearchDAO.hybrid_search(
                    query=request["query"],
                    filters=request["search_params"].get("filters"),
                    topk=request["search_params"].get("final_topk", 5),
                    bm25_topk=request["search_params"].get("bm25_topk", 12),
                    vector_topk=request["search_params"].get("vector_topk", 12),
                    rerank_candidates=request["search_params"].get("rerank_candidates", 50)
                )

                return result

        except Exception as e:
            logger.error(f"Single search execution failed for query '{request['query']}': {e}")
            raise

    def _generate_request_id(self, query: str, search_params: Dict[str, Any]) -> str:
        """요청 ID 생성"""
        content = f"{query}:{sorted(search_params.items())}"
        return hashlib.md5(content.encode()).hexdigest()

    def _update_metrics(self, batch_size: int, processing_time_ms: float):
        """메트릭 업데이트"""
        self.metrics.total_batches += 1
        self.metrics.total_items_processed += batch_size

        # 이동 평균 계산
        if self.metrics.total_batches > 1:
            self.metrics.avg_batch_size = (
                self.metrics.avg_batch_size * (self.metrics.total_batches - 1) + batch_size
            ) / self.metrics.total_batches

            self.metrics.avg_processing_time_ms = (
                self.metrics.avg_processing_time_ms * (self.metrics.total_batches - 1) + processing_time_ms
            ) / self.metrics.total_batches
        else:
            self.metrics.avg_batch_size = batch_size
            self.metrics.avg_processing_time_ms = processing_time_ms

        # 처리량 계산
        if processing_time_ms > 0:
            self.metrics.throughput_items_per_sec = (batch_size / processing_time_ms) * 1000

        # 캐시 히트율
        total_cache_requests = self.cache_hits + self.cache_misses
        if total_cache_requests > 0:
            self.metrics.cache_hit_rate = self.cache_hits / total_cache_requests

    def get_metrics(self) -> BatchMetrics:
        """메트릭 반환"""
        return self.metrics

    async def cleanup(self):
        """리소스 정리"""
        # 남은 요청들 플러시
        async with self.processing_lock:
            if self.pending_requests:
                await self._flush_batch()

        # 플러시 태스크 취소
        if self.flush_task:
            self.flush_task.cancel()

        # 캐시 정리
        self.embedding_cache.clear()

class BatchEmbeddingProcessor:
    """배치 임베딩 처리기"""

    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self.processing_stats = {
            "total_batches": 0,
            "total_embeddings": 0,
            "avg_batch_time": 0.0,
            "embeddings_per_second": 0.0
        }

    async def generate_batch_embeddings(
        self,
        texts: List[str],
        model: str = "openai"
    ) -> List[List[float]]:
        """
        대량 텍스트에 대한 배치 임베딩 생성

        Args:
            texts: 텍스트 리스트
            model: 임베딩 모델

        Returns:
            임베딩 리스트
        """
        all_embeddings = []
        total_start_time = time.time()

        # 배치 단위로 처리
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i + self.batch_size]
            batch_start_time = time.time()

            try:
                # 병렬 임베딩 생성
                batch_embeddings = await self._process_embedding_batch(batch_texts, model)
                all_embeddings.extend(batch_embeddings)

                # 통계 업데이트
                batch_time = time.time() - batch_start_time
                self._update_embedding_stats(len(batch_texts), batch_time)

                # API 레이트 리밋 고려 (배치 간 대기)
                if i + self.batch_size < len(texts):
                    await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Batch embedding generation failed: {e}")
                # 폴백: 더미 임베딩 생성
                from ..database import EmbeddingService
                fallback_embeddings = []
                for text in batch_texts:
                    fallback_embedding = EmbeddingService._get_dummy_embedding(text)
                    fallback_embeddings.append(fallback_embedding)
                all_embeddings.extend(fallback_embeddings)

        total_time = time.time() - total_start_time
        logger.info(
            f"Generated {len(all_embeddings)} embeddings in {total_time:.2f}s "
            f"({len(all_embeddings)/total_time:.1f} embeddings/sec)"
        )

        return all_embeddings

    async def _process_embedding_batch(
        self,
        batch_texts: List[str],
        model: str
    ) -> List[List[float]]:
        """배치 임베딩 처리"""
        # 동시 임베딩 생성 (제한적 병렬화)
        from ..database import EmbeddingService

        semaphore = asyncio.Semaphore(5)  # 최대 5개 동시 요청

        async def generate_single_embedding(text: str) -> List[float]:
            async with semaphore:
                return await EmbeddingService.generate_embedding(text, model)

        # 배치 내 병렬 처리
        embedding_tasks = [
            generate_single_embedding(text) for text in batch_texts
        ]

        embeddings = await asyncio.gather(
            *embedding_tasks,
            return_exceptions=True
        )

        # 예외 처리
        processed_embeddings = []
        for i, embedding in enumerate(embeddings):
            if isinstance(embedding, Exception):
                logger.warning(f"Embedding generation failed for text {i}: {embedding}")
                # 폴백 임베딩 사용
                fallback = EmbeddingService._get_dummy_embedding(batch_texts[i])
                processed_embeddings.append(fallback)
            else:
                processed_embeddings.append(embedding)

        return processed_embeddings

    def _update_embedding_stats(self, batch_size: int, batch_time: float):
        """임베딩 통계 업데이트"""
        self.processing_stats["total_batches"] += 1
        self.processing_stats["total_embeddings"] += batch_size

        # 이동 평균
        total_batches = self.processing_stats["total_batches"]
        current_avg = self.processing_stats["avg_batch_time"]
        self.processing_stats["avg_batch_time"] = (
            (current_avg * (total_batches - 1) + batch_time) / total_batches
        )

        # 처리 속도
        if batch_time > 0:
            self.processing_stats["embeddings_per_second"] = batch_size / batch_time

    def get_embedding_stats(self) -> Dict[str, Any]:
        """임베딩 처리 통계"""
        return self.processing_stats.copy()

class BatchConnectionPool:
    """배치 처리용 최적화된 연결 풀"""

    def __init__(self, max_connections: int = 50):
        self.max_connections = max_connections
        self.active_connections = 0
        self.connection_semaphore = asyncio.Semaphore(max_connections)
        self.connection_stats = {
            "total_acquisitions": 0,
            "total_wait_time": 0.0,
            "peak_usage": 0,
            "avg_utilization": 0.0
        }

    async def execute_batch_with_pool(
        self,
        batch_operations: List[callable],
        max_concurrent: int = None
    ) -> List[Any]:
        """
        연결 풀을 사용한 배치 실행

        Args:
            batch_operations: 실행할 작업 리스트
            max_concurrent: 최대 동시 실행 수

        Returns:
            결과 리스트
        """
        if max_concurrent is None:
            max_concurrent = min(self.max_connections, len(batch_operations))

        # 세마포어로 동시 연결 수 제한
        execution_semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_with_connection(operation):
            start_wait = time.time()

            async with execution_semaphore:
                async with self.connection_semaphore:
                    wait_time = time.time() - start_wait

                    # 통계 업데이트
                    self.connection_stats["total_acquisitions"] += 1
                    self.connection_stats["total_wait_time"] += wait_time

                    self.active_connections += 1
                    self.connection_stats["peak_usage"] = max(
                        self.connection_stats["peak_usage"],
                        self.active_connections
                    )

                    try:
                        return await operation()
                    finally:
                        self.active_connections -= 1

        # 모든 작업 병렬 실행
        results = await asyncio.gather(
            *[execute_with_connection(op) for op in batch_operations],
            return_exceptions=True
        )

        # 평균 사용률 계산
        if self.connection_stats["total_acquisitions"] > 0:
            total_acquisitions = self.connection_stats["total_acquisitions"]
            peak_usage = self.connection_stats["peak_usage"]
            self.connection_stats["avg_utilization"] = peak_usage / self.max_connections

        return results

    def get_connection_stats(self) -> Dict[str, Any]:
        """연결 풀 통계"""
        stats = self.connection_stats.copy()
        stats.update({
            "max_connections": self.max_connections,
            "active_connections": self.active_connections,
            "available_connections": self.max_connections - self.active_connections,
            "utilization": self.active_connections / self.max_connections
        })

        if stats["total_acquisitions"] > 0:
            stats["avg_wait_time"] = stats["total_wait_time"] / stats["total_acquisitions"]

        return stats

# 전역 배치 프로세서 인스턴스들
_global_search_processor = None
_global_embedding_processor = None
_global_connection_pool = None

def get_batch_search_processor() -> BatchSearchProcessor:
    """전역 배치 검색 프로세서"""
    global _global_search_processor
    if _global_search_processor is None:
        config = BatchConfig(
            max_batch_size=50,
            max_wait_time_ms=100,
            auto_flush=True,
            enable_prioritization=True
        )
        _global_search_processor = BatchSearchProcessor(config)
    return _global_search_processor

def get_batch_embedding_processor() -> BatchEmbeddingProcessor:
    """전역 배치 임베딩 프로세서"""
    global _global_embedding_processor
    if _global_embedding_processor is None:
        _global_embedding_processor = BatchEmbeddingProcessor(batch_size=100)
    return _global_embedding_processor

def get_batch_connection_pool() -> BatchConnectionPool:
    """전역 배치 연결 풀"""
    global _global_connection_pool
    if _global_connection_pool is None:
        _global_connection_pool = BatchConnectionPool(max_connections=50)
    return _global_connection_pool