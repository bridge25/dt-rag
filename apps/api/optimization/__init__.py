"""
성능 최적화 모듈
HYBRID_SEARCH_OPTIMIZATION_GUIDE.md 기반 구현

모듈 구성:
- async_executor: 비동기 병렬 처리 최적화
- memory_optimizer: 메모리 사용량 최적화 및 가비지 컬렉션
- concurrency_control: 동시성 제어 및 리소스 관리
- batch_processor: 배치 처리 및 연결 풀 최적화
"""

from .async_executor import (
    AsyncExecutionOptimizer,
    BatchProcessor,
    get_async_optimizer,
    async_search_context
)

from .memory_optimizer import (
    EmbeddingQuantizer,
    StreamingResultProcessor,
    GarbageCollectionOptimizer,
    MemoryMonitor,
    get_embedding_quantizer,
    get_streaming_processor,
    get_gc_optimizer,
    get_memory_monitor
)

from .concurrency_control import (
    CircuitBreaker,
    AdaptiveRateLimiter,
    ResourcePool,
    ConcurrencyController,
    CircuitBreakerException,
    RateLimitExceededException,
    get_concurrency_controller
)

from .batch_processor import (
    BatchSearchProcessor,
    BatchEmbeddingProcessor,
    BatchConnectionPool,
    get_batch_search_processor,
    get_batch_embedding_processor,
    get_batch_connection_pool
)

__all__ = [
    # 비동기 실행 최적화
    "AsyncExecutionOptimizer",
    "BatchProcessor",
    "get_async_optimizer",
    "async_search_context",

    # 메모리 최적화
    "EmbeddingQuantizer",
    "StreamingResultProcessor",
    "GarbageCollectionOptimizer",
    "MemoryMonitor",
    "get_embedding_quantizer",
    "get_streaming_processor",
    "get_gc_optimizer",
    "get_memory_monitor",

    # 동시성 제어
    "CircuitBreaker",
    "AdaptiveRateLimiter",
    "ResourcePool",
    "ConcurrencyController",
    "CircuitBreakerException",
    "RateLimitExceededException",
    "get_concurrency_controller",

    # 배치 처리
    "BatchSearchProcessor",
    "BatchEmbeddingProcessor",
    "BatchConnectionPool",
    "get_batch_search_processor",
    "get_batch_embedding_processor",
    "get_batch_connection_pool"
]

# 최적화 모듈 버전
__version__ = "1.0.0"

# 성능 목표 상수
PERFORMANCE_TARGETS = {
    "p95_latency_ms": 100,      # P95 응답시간 100ms 이하
    "throughput_qps": 50,        # 50 QPS 이상
    "cache_hit_rate": 0.70,      # 캐시 히트율 70% 이상
    "memory_efficiency": 0.50,    # 메모리 효율성 50% 향상
    "parallel_speedup": 2.0,      # 병렬화 2배 이상 성능 향상
    "error_rate": 0.01           # 오류율 1% 이하
}

def get_optimization_status():
    """최적화 모듈 상태 반환"""
    return {
        "version": __version__,
        "modules": {
            "async_executor": "available",
            "memory_optimizer": "available",
            "concurrency_control": "available",
            "batch_processor": "available"
        },
        "performance_targets": PERFORMANCE_TARGETS,
        "status": "ready"
    }