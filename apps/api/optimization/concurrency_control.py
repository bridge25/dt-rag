"""
동시성 제어 및 리소스 관리 시스템
HYBRID_SEARCH_OPTIMIZATION_GUIDE.md 동시성 최적화 구현

핵심 기능:
- Semaphore 기반 동시 요청 제한
- Circuit Breaker 패턴 구현
- 적응형 레이트 리미팅
- 리소스 풀 관리
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager
import threading
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit Breaker 상태"""
    CLOSED = "closed"        # 정상 동작
    OPEN = "open"           # 장애 상태 (요청 차단)
    HALF_OPEN = "half_open" # 복구 확인 중

@dataclass
class CircuitBreakerConfig:
    """Circuit Breaker 설정"""
    failure_threshold: int = 5      # 실패 임계치
    timeout_seconds: int = 60       # 타임아웃 시간
    success_threshold: int = 3      # 복구 확인용 성공 임계치
    window_size: int = 100         # 슬라이딩 윈도우 크기

@dataclass
class RateLimitConfig:
    """레이트 리밋 설정"""
    requests_per_second: float = 10.0    # 초당 요청 수
    burst_size: int = 20                 # 버스트 크기
    window_size_seconds: int = 60        # 윈도우 크기
    adaptive: bool = True                # 적응형 여부

@dataclass
class ConcurrencyMetrics:
    """동시성 메트릭"""
    active_requests: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rate_limited_requests: int = 0
    circuit_breaker_trips: int = 0
    avg_response_time: float = 0.0
    peak_concurrency: int = 0
    timestamp: float = field(default_factory=time.time)

class CircuitBreaker:
    """Circuit Breaker 패턴 구현"""

    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.request_history = deque(maxlen=config.window_size)
        self._lock = threading.Lock()

    async def call(self, func: Callable[..., Awaitable], *args, **kwargs):
        """Circuit Breaker로 함수 호출"""
        if not await self._can_proceed():
            raise CircuitBreakerException(
                f"Circuit breaker {self.name} is OPEN"
            )

        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            await self._record_success(time.time() - start_time)
            return result

        except Exception as e:
            await self._record_failure(time.time() - start_time)
            raise

    async def _can_proceed(self) -> bool:
        """요청 진행 가능 여부 확인"""
        with self._lock:
            current_time = time.time()

            if self.state == CircuitState.CLOSED:
                return True

            elif self.state == CircuitState.OPEN:
                # 타임아웃 경과 시 HALF_OPEN으로 전환
                if current_time - self.last_failure_time >= self.config.timeout_seconds:
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info(f"Circuit breaker {self.name} moved to HALF_OPEN")
                    return True
                return False

            elif self.state == CircuitState.HALF_OPEN:
                return True

        return False

    async def _record_success(self, response_time: float):
        """성공 기록"""
        with self._lock:
            self.request_history.append({"success": True, "time": response_time})

            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    logger.info(f"Circuit breaker {self.name} moved to CLOSED")

    async def _record_failure(self, response_time: float):
        """실패 기록"""
        with self._lock:
            self.request_history.append({"success": False, "time": response_time})
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.state == CircuitState.CLOSED:
                # 최근 윈도우 내 실패율 확인
                recent_requests = list(self.request_history)[-self.config.window_size:]
                if len(recent_requests) >= self.config.failure_threshold:
                    failures = sum(1 for req in recent_requests if not req["success"])
                    failure_rate = failures / len(recent_requests)

                    if failure_rate >= 0.5:  # 50% 실패율
                        self.state = CircuitState.OPEN
                        logger.warning(
                            f"Circuit breaker {self.name} OPENED due to high failure rate: {failure_rate:.2f}"
                        )

            elif self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker {self.name} moved back to OPEN")

    def get_stats(self) -> Dict[str, Any]:
        """Circuit Breaker 통계"""
        with self._lock:
            recent_requests = list(self.request_history)
            total_requests = len(recent_requests)
            successful_requests = sum(1 for req in recent_requests if req["success"])

            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "total_requests": total_requests,
                "success_rate": successful_requests / total_requests if total_requests > 0 else 0,
                "avg_response_time": sum(req["time"] for req in recent_requests) / total_requests if total_requests > 0 else 0,
                "last_failure_time": self.last_failure_time
            }

class AdaptiveRateLimiter:
    """적응형 레이트 리미터"""

    def __init__(self, name: str, config: RateLimitConfig):
        self.name = name
        self.config = config
        self.tokens = float(config.burst_size)
        self.last_update = time.time()
        self.request_times = deque()
        self.adaptive_rate = config.requests_per_second
        self._lock = threading.Lock()

    async def acquire(self) -> bool:
        """토큰 획득 시도"""
        with self._lock:
            current_time = time.time()

            # 토큰 보충
            self._replenish_tokens(current_time)

            # 적응형 레이트 조정
            if self.config.adaptive:
                self._adjust_adaptive_rate(current_time)

            # 토큰 확인
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                self.request_times.append(current_time)
                return True
            else:
                return False

    def _replenish_tokens(self, current_time: float):
        """토큰 보충"""
        time_passed = current_time - self.last_update
        tokens_to_add = time_passed * self.adaptive_rate

        self.tokens = min(
            self.config.burst_size,
            self.tokens + tokens_to_add
        )
        self.last_update = current_time

    def _adjust_adaptive_rate(self, current_time: float):
        """적응형 레이트 조정"""
        # 최근 요청 수 계산
        cutoff_time = current_time - self.config.window_size_seconds
        recent_requests = [
            req_time for req_time in self.request_times
            if req_time > cutoff_time
        ]

        if len(recent_requests) < self.config.window_size_seconds * 0.1:
            # 요청이 적으면 레이트 증가
            self.adaptive_rate = min(
                self.config.requests_per_second * 2,
                self.adaptive_rate * 1.1
            )
        elif len(recent_requests) > self.config.window_size_seconds * 0.8:
            # 요청이 많으면 레이트 감소
            self.adaptive_rate = max(
                self.config.requests_per_second * 0.5,
                self.adaptive_rate * 0.9
            )

        # 오래된 요청 시간 제거
        while self.request_times and self.request_times[0] <= cutoff_time:
            self.request_times.popleft()

    def get_stats(self) -> Dict[str, Any]:
        """레이트 리미터 통계"""
        with self._lock:
            current_time = time.time()
            cutoff_time = current_time - self.config.window_size_seconds
            recent_requests = [
                req_time for req_time in self.request_times
                if req_time > cutoff_time
            ]

            return {
                "name": self.name,
                "current_rate": self.adaptive_rate,
                "configured_rate": self.config.requests_per_second,
                "available_tokens": self.tokens,
                "burst_size": self.config.burst_size,
                "recent_requests": len(recent_requests),
                "recent_rps": len(recent_requests) / self.config.window_size_seconds if recent_requests else 0
            }

class ResourcePool:
    """리소스 풀 관리"""

    def __init__(self, name: str, max_size: int = 20):
        self.name = name
        self.max_size = max_size
        self.semaphore = asyncio.Semaphore(max_size)
        self.active_resources = 0
        self.waiting_count = 0
        self.total_acquisitions = 0
        self.total_wait_time = 0.0
        self._lock = threading.Lock()

    @asynccontextmanager
    async def acquire(self):
        """리소스 획득"""
        start_wait = time.time()

        with self._lock:
            self.waiting_count += 1

        try:
            async with self.semaphore:
                wait_time = time.time() - start_wait

                with self._lock:
                    self.waiting_count -= 1
                    self.active_resources += 1
                    self.total_acquisitions += 1
                    self.total_wait_time += wait_time

                try:
                    yield
                finally:
                    with self._lock:
                        self.active_resources -= 1

        except Exception:
            with self._lock:
                self.waiting_count -= 1
            raise

    def get_stats(self) -> Dict[str, Any]:
        """리소스 풀 통계"""
        with self._lock:
            return {
                "name": self.name,
                "max_size": self.max_size,
                "active_resources": self.active_resources,
                "waiting_count": self.waiting_count,
                "available": self.max_size - self.active_resources,
                "utilization": self.active_resources / self.max_size,
                "total_acquisitions": self.total_acquisitions,
                "avg_wait_time": self.total_wait_time / self.total_acquisitions if self.total_acquisitions > 0 else 0
            }

class ConcurrencyController:
    """통합 동시성 제어"""

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.rate_limiters: Dict[str, AdaptiveRateLimiter] = {}
        self.resource_pools: Dict[str, ResourcePool] = {}
        self.metrics = ConcurrencyMetrics()
        self._lock = threading.Lock()

    def add_circuit_breaker(
        self,
        name: str,
        config: CircuitBreakerConfig = None
    ) -> CircuitBreaker:
        """Circuit Breaker 추가"""
        if config is None:
            config = CircuitBreakerConfig()

        circuit_breaker = CircuitBreaker(name, config)
        self.circuit_breakers[name] = circuit_breaker
        return circuit_breaker

    def add_rate_limiter(
        self,
        name: str,
        config: RateLimitConfig = None
    ) -> AdaptiveRateLimiter:
        """Rate Limiter 추가"""
        if config is None:
            config = RateLimitConfig()

        rate_limiter = AdaptiveRateLimiter(name, config)
        self.rate_limiters[name] = rate_limiter
        return rate_limiter

    def add_resource_pool(
        self,
        name: str,
        max_size: int = 20
    ) -> ResourcePool:
        """리소스 풀 추가"""
        resource_pool = ResourcePool(name, max_size)
        self.resource_pools[name] = resource_pool
        return resource_pool

    @asynccontextmanager
    async def controlled_execution(
        self,
        operation_name: str,
        use_circuit_breaker: bool = True,
        use_rate_limiter: bool = True,
        use_resource_pool: bool = True
    ):
        """제어된 실행 컨텍스트"""
        start_time = time.time()

        # 메트릭 업데이트
        with self._lock:
            self.metrics.active_requests += 1
            self.metrics.total_requests += 1
            self.metrics.peak_concurrency = max(
                self.metrics.peak_concurrency,
                self.metrics.active_requests
            )

        try:
            # Rate Limiting 체크
            if use_rate_limiter and operation_name in self.rate_limiters:
                if not await self.rate_limiters[operation_name].acquire():
                    with self._lock:
                        self.metrics.rate_limited_requests += 1
                    raise RateLimitExceededException(f"Rate limit exceeded for {operation_name}")

            # Resource Pool 획득
            resource_context = None
            if use_resource_pool and operation_name in self.resource_pools:
                resource_context = self.resource_pools[operation_name].acquire()
                await resource_context.__aenter__()

            try:
                yield

                # 성공 시 메트릭 업데이트
                with self._lock:
                    self.metrics.successful_requests += 1

            finally:
                if resource_context:
                    await resource_context.__aexit__(None, None, None)

        except Exception as e:
            # 실패 시 메트릭 업데이트
            with self._lock:
                self.metrics.failed_requests += 1
            raise

        finally:
            # 응답 시간 및 활성 요청 수 업데이트
            response_time = time.time() - start_time

            with self._lock:
                self.metrics.active_requests -= 1

                # 이동 평균으로 응답 시간 계산
                if self.metrics.total_requests > 1:
                    self.metrics.avg_response_time = (
                        self.metrics.avg_response_time * (self.metrics.total_requests - 1) + response_time
                    ) / self.metrics.total_requests
                else:
                    self.metrics.avg_response_time = response_time

    async def execute_with_circuit_breaker(
        self,
        name: str,
        func: Callable[..., Awaitable],
        *args,
        **kwargs
    ):
        """Circuit Breaker로 함수 실행"""
        if name not in self.circuit_breakers:
            # 기본 Circuit Breaker 생성
            self.add_circuit_breaker(name)

        return await self.circuit_breakers[name].call(func, *args, **kwargs)

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """종합 통계"""
        with self._lock:
            stats = {
                "timestamp": time.time(),
                "metrics": {
                    "active_requests": self.metrics.active_requests,
                    "total_requests": self.metrics.total_requests,
                    "successful_requests": self.metrics.successful_requests,
                    "failed_requests": self.metrics.failed_requests,
                    "rate_limited_requests": self.metrics.rate_limited_requests,
                    "success_rate": self.metrics.successful_requests / max(1, self.metrics.total_requests),
                    "error_rate": self.metrics.failed_requests / max(1, self.metrics.total_requests),
                    "avg_response_time": self.metrics.avg_response_time,
                    "peak_concurrency": self.metrics.peak_concurrency
                },
                "circuit_breakers": {
                    name: cb.get_stats()
                    for name, cb in self.circuit_breakers.items()
                },
                "rate_limiters": {
                    name: rl.get_stats()
                    for name, rl in self.rate_limiters.items()
                },
                "resource_pools": {
                    name: rp.get_stats()
                    for name, rp in self.resource_pools.items()
                }
            }

        return stats

    def reset_metrics(self):
        """메트릭 초기화"""
        with self._lock:
            self.metrics = ConcurrencyMetrics()

# 예외 클래스들
class CircuitBreakerException(Exception):
    """Circuit Breaker 예외"""
    pass

class RateLimitExceededException(Exception):
    """Rate Limit 초과 예외"""
    pass

# 전역 동시성 제어기
_global_concurrency_controller = None

def get_concurrency_controller() -> ConcurrencyController:
    """전역 동시성 제어기 반환"""
    global _global_concurrency_controller

    if _global_concurrency_controller is None:
        _global_concurrency_controller = ConcurrencyController()

        # 기본 Circuit Breaker들 설정
        _global_concurrency_controller.add_circuit_breaker(
            "search",
            CircuitBreakerConfig(failure_threshold=5, timeout_seconds=60)
        )
        _global_concurrency_controller.add_circuit_breaker(
            "embedding",
            CircuitBreakerConfig(failure_threshold=3, timeout_seconds=30)
        )

        # 기본 Rate Limiter들 설정
        _global_concurrency_controller.add_rate_limiter(
            "search",
            RateLimitConfig(requests_per_second=50.0, burst_size=100)
        )
        _global_concurrency_controller.add_rate_limiter(
            "embedding",
            RateLimitConfig(requests_per_second=20.0, burst_size=40)
        )

        # 기본 리소스 풀들 설정
        _global_concurrency_controller.add_resource_pool("database", 20)
        _global_concurrency_controller.add_resource_pool("api_calls", 10)

    return _global_concurrency_controller