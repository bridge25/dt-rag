"""
비동기 병렬 처리 최적화 엔진
HYBRID_SEARCH_OPTIMIZATION_GUIDE.md 기준 구현

핵심 기능:
- BM25 + Vector 검색 병렬 실행
- 동시성 제어 및 세마포어 관리
- CPU 집약적 작업 ThreadPool 분리
- 메모리 최적화 및 가비지 컬렉션
"""

import asyncio
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional, Tuple, Coroutine
from contextlib import asynccontextmanager
import threading
import gc
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ExecutionMetrics:
    """실행 메트릭"""
    total_time: float
    parallel_time: float
    cpu_intensive_time: float
    memory_usage: Dict[str, float]
    concurrency_level: int
    tasks_completed: int

class AsyncExecutionOptimizer:
    """비동기 실행 최적화 엔진"""

    def __init__(
        self,
        max_concurrent_searches: int = 10,
        cpu_workers: int = 4,
        memory_threshold_mb: int = 1024
    ):
        """
        Args:
            max_concurrent_searches: 최대 동시 검색 수
            cpu_workers: CPU 작업용 쓰레드 풀 크기
            memory_threshold_mb: 메모리 임계치 (MB)
        """
        # 세마포어 설정 (동시 요청 제한)
        self.search_semaphore = asyncio.Semaphore(max_concurrent_searches)
        self.fusion_semaphore = asyncio.Semaphore(max_concurrent_searches // 2)

        # ThreadPool for CPU-intensive tasks
        self.cpu_executor = ThreadPoolExecutor(
            max_workers=cpu_workers,
            thread_name_prefix="cpu_intensive"
        )

        # 메모리 관리
        self.memory_threshold = memory_threshold_mb * 1024 * 1024  # bytes

        # 성능 메트릭
        self.execution_metrics = []
        self._lock = threading.Lock()

        # 병렬 실행 통계
        self.parallel_stats = {
            "total_parallel_searches": 0,
            "avg_speedup": 0.0,
            "parallel_vs_sequential_ratio": 0.0
        }

    async def execute_parallel_search(
        self,
        session,
        query: str,
        query_embedding: List[float],
        search_params: Dict[str, Any]
    ) -> Tuple[List[Dict], List[Dict], ExecutionMetrics]:
        """
        BM25 + Vector 검색 병렬 실행

        Returns:
            Tuple[bm25_results, vector_results, metrics]
        """
        start_time = time.time()

        async with self.search_semaphore:
            try:
                # 메모리 사용량 체크
                await self._check_memory_usage()

                # BM25와 Vector 검색 병렬 실행
                bm25_task = self._create_bm25_task(session, query, search_params)
                vector_task = self._create_vector_task(session, query_embedding, search_params)

                parallel_start = time.time()

                # asyncio.gather로 병렬 실행
                bm25_results, vector_results = await asyncio.gather(
                    bm25_task,
                    vector_task,
                    return_exceptions=True
                )

                parallel_time = time.time() - parallel_start

                # 예외 처리
                if isinstance(bm25_results, Exception):
                    logger.error(f"BM25 search failed: {bm25_results}")
                    bm25_results = []

                if isinstance(vector_results, Exception):
                    logger.error(f"Vector search failed: {vector_results}")
                    vector_results = []

                # 실행 메트릭 수집
                total_time = time.time() - start_time
                metrics = ExecutionMetrics(
                    total_time=total_time,
                    parallel_time=parallel_time,
                    cpu_intensive_time=0.0,
                    memory_usage=await self._get_memory_usage(),
                    concurrency_level=self.search_semaphore._value,
                    tasks_completed=2
                )

                # 통계 업데이트
                await self._update_parallel_stats(metrics)

                return bm25_results, vector_results, metrics

            except Exception as e:
                logger.error(f"Parallel search execution failed: {e}")
                raise

    async def execute_cpu_intensive_task(
        self,
        task_func,
        *args,
        **kwargs
    ) -> Any:
        """
        CPU 집약적 작업을 ThreadPool에서 실행

        Args:
            task_func: 실행할 함수
            *args, **kwargs: 함수 인자
        """
        start_time = time.time()

        try:
            # ThreadPool에서 실행
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.cpu_executor,
                task_func,
                *args,
                **kwargs
            )

            cpu_time = time.time() - start_time
            logger.debug(f"CPU intensive task completed in {cpu_time:.3f}s")

            return result

        except Exception as e:
            logger.error(f"CPU intensive task failed: {e}")
            raise

    async def execute_fusion_with_concurrency_control(
        self,
        bm25_results: List[Dict],
        vector_results: List[Dict],
        fusion_params: Dict[str, Any]
    ) -> List[Dict]:
        """
        동시성 제어가 적용된 결과 융합
        """
        async with self.fusion_semaphore:
            try:
                # CPU 집약적 융합 작업을 ThreadPool에서 실행
                fused_results = await self.execute_cpu_intensive_task(
                    self._fusion_function,
                    bm25_results,
                    vector_results,
                    fusion_params
                )

                return fused_results

            except Exception as e:
                logger.error(f"Fusion with concurrency control failed: {e}")
                raise

    def _fusion_function(
        self,
        bm25_results: List[Dict],
        vector_results: List[Dict],
        fusion_params: Dict[str, Any]
    ) -> List[Dict]:
        """
        실제 융합 로직 (CPU 집약적)
        """
        try:
            # 결과 합성 및 중복 제거
            combined = {}

            # BM25 결과 추가
            for result in bm25_results:
                chunk_id = result["chunk_id"]
                combined[chunk_id] = result.copy()

            # Vector 결과 추가/업데이트
            bm25_weight = fusion_params.get("bm25_weight", 0.5)
            vector_weight = fusion_params.get("vector_weight", 0.5)

            for result in vector_results:
                chunk_id = result["chunk_id"]
                if chunk_id in combined:
                    # 하이브리드 스코어 계산
                    bm25_score = combined[chunk_id]["metadata"]["bm25_score"]
                    vector_score = result["metadata"]["vector_score"]

                    combined[chunk_id]["score"] = (
                        bm25_weight * bm25_score + vector_weight * vector_score
                    )
                    combined[chunk_id]["metadata"]["vector_score"] = vector_score
                    combined[chunk_id]["metadata"]["source"] = "hybrid"
                else:
                    combined[chunk_id] = result.copy()

            # 점수순 정렬
            sorted_results = sorted(
                combined.values(),
                key=lambda x: x["score"],
                reverse=True
            )

            return sorted_results[:fusion_params.get("max_candidates", 50)]

        except Exception as e:
            logger.error(f"Fusion function failed: {e}")
            return []

    async def _create_bm25_task(
        self,
        session,
        query: str,
        search_params: Dict[str, Any]
    ) -> Coroutine:
        """BM25 검색 태스크 생성"""
        from ..database import SearchDAO

        return SearchDAO._perform_bm25_search(
            session=session,
            query=query,
            topk=search_params.get("bm25_topk", 12),
            filters=search_params.get("filters")
        )

    async def _create_vector_task(
        self,
        session,
        query_embedding: List[float],
        search_params: Dict[str, Any]
    ) -> Coroutine:
        """Vector 검색 태스크 생성"""
        from ..database import SearchDAO

        return SearchDAO._perform_vector_search(
            session=session,
            query_embedding=query_embedding,
            topk=search_params.get("vector_topk", 12),
            filters=search_params.get("filters")
        )

    async def _check_memory_usage(self):
        """메모리 사용량 체크 및 정리"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()

            if memory_info.rss > self.memory_threshold:
                logger.warning(
                    f"Memory usage high: {memory_info.rss / 1024 / 1024:.1f}MB, "
                    f"triggering garbage collection"
                )
                # 강제 가비지 컬렉션
                gc.collect()

        except ImportError:
            # psutil 없으면 기본 가비지 컬렉션만
            gc.collect()

    async def _get_memory_usage(self) -> Dict[str, float]:
        """현재 메모리 사용량 반환"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()

            return {
                "rss_mb": memory_info.rss / 1024 / 1024,
                "vms_mb": memory_info.vms / 1024 / 1024,
                "percent": process.memory_percent()
            }
        except ImportError:
            return {"rss_mb": 0, "vms_mb": 0, "percent": 0}

    async def _update_parallel_stats(self, metrics: ExecutionMetrics):
        """병렬 실행 통계 업데이트"""
        with self._lock:
            self.execution_metrics.append(metrics)

            # 최근 100개 메트릭만 유지
            if len(self.execution_metrics) > 100:
                self.execution_metrics = self.execution_metrics[-100:]

            # 통계 계산
            if len(self.execution_metrics) >= 2:
                total_searches = len(self.execution_metrics)
                avg_parallel_time = sum(m.parallel_time for m in self.execution_metrics) / total_searches

                # 순차 실행 시간 추정 (병렬 시간의 2배로 가정)
                estimated_sequential_time = avg_parallel_time * 2
                speedup = estimated_sequential_time / avg_parallel_time if avg_parallel_time > 0 else 1.0

                self.parallel_stats.update({
                    "total_parallel_searches": total_searches,
                    "avg_speedup": speedup,
                    "parallel_vs_sequential_ratio": avg_parallel_time / estimated_sequential_time
                })

    def get_performance_stats(self) -> Dict[str, Any]:
        """성능 통계 반환"""
        with self._lock:
            if not self.execution_metrics:
                return {"no_data": True}

            recent_metrics = self.execution_metrics[-10:]  # 최근 10개

            return {
                "parallel_stats": self.parallel_stats.copy(),
                "recent_performance": {
                    "avg_total_time": sum(m.total_time for m in recent_metrics) / len(recent_metrics),
                    "avg_parallel_time": sum(m.parallel_time for m in recent_metrics) / len(recent_metrics),
                    "avg_memory_usage": sum(m.memory_usage.get("rss_mb", 0) for m in recent_metrics) / len(recent_metrics),
                    "avg_concurrency": sum(m.concurrency_level for m in recent_metrics) / len(recent_metrics)
                },
                "resource_utilization": {
                    "semaphore_availability": {
                        "search": self.search_semaphore._value,
                        "fusion": self.fusion_semaphore._value
                    },
                    "thread_pool": {
                        "active_threads": len(self.cpu_executor._threads) if hasattr(self.cpu_executor, '_threads') else 0,
                        "max_workers": self.cpu_executor._max_workers
                    }
                }
            }

    async def cleanup(self):
        """리소스 정리"""
        try:
            # ThreadPool 종료
            self.cpu_executor.shutdown(wait=True)

            # 메트릭 정리
            self.execution_metrics.clear()

            logger.info("AsyncExecutionOptimizer cleanup completed")

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

class BatchProcessor:
    """배치 처리 최적화"""

    def __init__(self, batch_size: int = 10, max_batches: int = 5):
        self.batch_size = batch_size
        self.max_batches = max_batches

    async def process_search_batch(
        self,
        queries: List[str],
        search_func,
        **search_kwargs
    ) -> List[List[Dict]]:
        """
        여러 쿼리를 배치로 병렬 처리

        Args:
            queries: 검색 쿼리 리스트
            search_func: 검색 함수
            **search_kwargs: 검색 함수 인자
        """
        results = []

        # 배치 단위로 분할
        for i in range(0, len(queries), self.batch_size):
            batch_queries = queries[i:i + self.batch_size]

            # 배치 내 쿼리들을 병렬 실행
            batch_tasks = [
                search_func(query=query, **search_kwargs)
                for query in batch_queries
            ]

            batch_results = await asyncio.gather(
                *batch_tasks,
                return_exceptions=True
            )

            # 예외 처리
            processed_results = []
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch search failed: {result}")
                    processed_results.append([])
                else:
                    processed_results.append(result)

            results.extend(processed_results)

            # 배치 간 짧은 대기 (API 레이트 리밋 고려)
            if i + self.batch_size < len(queries):
                await asyncio.sleep(0.1)

        return results

# 전역 최적화 인스턴스
_global_optimizer = None

async def get_async_optimizer() -> AsyncExecutionOptimizer:
    """전역 최적화 인스턴스 반환"""
    global _global_optimizer

    if _global_optimizer is None:
        _global_optimizer = AsyncExecutionOptimizer(
            max_concurrent_searches=10,
            cpu_workers=4,
            memory_threshold_mb=1024
        )

    return _global_optimizer

@asynccontextmanager
async def async_search_context():
    """비동기 검색 컨텍스트 매니저"""
    optimizer = await get_async_optimizer()
    try:
        yield optimizer
    finally:
        # 컨텍스트 종료 시 메모리 정리
        await optimizer._check_memory_usage()